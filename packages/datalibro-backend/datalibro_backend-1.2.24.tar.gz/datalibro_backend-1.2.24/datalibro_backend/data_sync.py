#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
import random
import threading
import pymysql
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pandas as pd
import traceback
from typing import List, Dict, Any, Union, Optional, Callable, Tuple


class DataSyncUtils:
    """数据同步工具类，提供高效的数据库操作方法"""
    
    # 线程本地存储，用于连接复用
    _thread_local = threading.local()
    
    @staticmethod
    def default_batch_callback(batch_id: int, count: int, elapsed: float) -> None:
        """
        默认的批处理回调函数，输出批处理结果统计
        
        参数:
            batch_id: 批次ID
            count: 处理的记录数
            elapsed: 处理耗时(秒)
        """
        speed = count / elapsed if elapsed > 0 else 0
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 子批次 {batch_id} 完成: {count} 条记录, "
              f"耗时 {elapsed:.2f} 秒, 速率: {speed:.1f} 条/秒")
    
    @staticmethod
    def _build_connect_params(db_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建数据库连接参数
        
        参数:
            db_config: 数据库配置字典
            
        返回:
            pymysql连接参数字典
        """
        # 检查是否为TiDB，自动启用SSL
        db_type = str(db_config.get("db_type") or "unknown").lower()
        ssl_enabled = "ssl" in db_config and not db_config.get("ssl_disabled", False)
        
        if db_type == "tidb" and not ssl_enabled:
            db_config = dict(db_config)
            db_config["ssl"] = {}
            db_config["ssl_disabled"] = False
            ssl_enabled = True
        
        params = {
            "host": db_config["host"],
            "port": db_config["port"],
            "user": db_config["user"],
            "password": db_config["password"],
            "database": db_config["database"],
            "charset": db_config.get("charset", "utf8mb4"),
            "connect_timeout": db_config.get("connect_timeout", 10),
            "read_timeout": db_config.get("read_timeout", 30),
            "write_timeout": db_config.get("write_timeout", 30),
            "local_infile": db_config.get("local_infile", 1),
            "autocommit": False,
            "init_command": db_config.get("init_command", "SET tidb_txn_mode='optimistic'"),
            "max_allowed_packet": db_config.get("max_allowed_packet", 16 * 1024 * 1024),
        }
        
        if "ssl" in db_config and not db_config.get("ssl_disabled", False):
            params["ssl"] = db_config["ssl"]
            params["ssl_disabled"] = False
        elif db_config.get("ssl_disabled", False):
            params["ssl_disabled"] = True
        
        return params
    
    @staticmethod
    def _get_thread_connection(db_config: Dict[str, Any]) -> pymysql.connections.Connection:
        """
        获取当前线程的数据库连接（连接复用）
        
        参数:
            db_config: 数据库配置
            
        返回:
            pymysql连接对象
        """
        local = DataSyncUtils._thread_local
        conn = getattr(local, "conn", None)
        
        if conn is not None:
            try:
                conn.ping(reconnect=True)
                return conn
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None
        
        # 创建新连接
        conn = pymysql.connect(**DataSyncUtils._build_connect_params(db_config))
        local.conn = conn
        return conn
    
    @staticmethod
    def batch_insert_worker(
        batch_data: List[List[Any]], 
        insert_sql: str, 
        db_config: Dict[str, Any], 
        batch_id: int,
        callback: Optional[Callable] = None,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
        max_backoff: float = 10.0
    ) -> int:
        """
        并行批量插入工作线程 - 支持连接复用和重试机制
        
        参数:
            batch_data: 要插入的数据批次
            insert_sql: 预编译的插入SQL语句
            db_config: 数据库连接配置
            batch_id: 批次ID，用于日志
            callback: 可选的回调函数，处理每批次结果后调用
            max_retries: 最大重试次数，默认3次
            retry_backoff: 重试退避基数（秒），默认1.0
            max_backoff: 最大退避时间（秒），默认10.0
            
        返回:
            插入的记录数
        """
        start_time = time.time()
        attempt = 0
        
        while True:
            conn = None
            cursor = None
            try:
                # 获取线程连接（复用）
                conn = DataSyncUtils._get_thread_connection(db_config)
                cursor = conn.cursor()
                
                # 执行批量插入
                cursor.executemany(insert_sql, batch_data)
                conn.commit()
                
                elapsed = time.time() - start_time
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 批次 {batch_id} 完成: 插入 {len(batch_data)} 条记录, 耗时 {elapsed:.2f} 秒")
                
                # 如果有回调函数，则调用
                if callback:
                    callback(batch_id, len(batch_data), elapsed)
                    
                return len(batch_data)
                
            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                
                # 检查是否需要重试
                if attempt >= max_retries:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 批次 {batch_id} 失败(已重试{max_retries}次): {str(e)}")
                    raise e
                
                # 计算退避时间（指数退避 + 随机抖动）
                delay = min(max_backoff, retry_backoff * (2 ** attempt))
                delay += random.uniform(0, 0.5)
                
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 批次 {batch_id} 失败: {str(e)}, "
                      f"{delay:.2f}s 后重试 (attempt {attempt + 1}/{max_retries})")
                
                # 尝试重连
                try:
                    if conn:
                        conn.close()
                except Exception:
                    pass
                
                # 清除线程本地连接，下次会创建新连接
                DataSyncUtils._thread_local.conn = None
                
                time.sleep(delay)
                attempt += 1
                
            finally:
                if cursor:
                    try:
                        cursor.close()
                    except Exception:
                        pass
    
    @staticmethod
    def parallel_write_to_db(
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        db_config: Dict[str, Any],
        columns: List[str] = None,
        batch_size: int = 2000,
        max_workers: int = 20,
        insert_method: str = "update",
        primary_keys: List[str] = None,
        callback: Optional[Callable] = None,
        encrypted_columns: List[str] = None,
        encryption_key: str = "fake_encryption_key",
        max_retries: int = 3,
        retry_backoff: float = 1.0,
        max_backoff: float = 10.0
    ) -> Tuple[int, float, List[str]]:
        """
        并行写入数据到数据库 - 支持连接复用和重试机制
        
        参数:
            data: 要写入的数据，可以是Pandas DataFrame或字典列表
            db_config: 数据库连接配置，必须包含host, port, user, password, database, table等字段
            columns: 列名列表，如果为None则从data中推断
            batch_size: 每批次处理的记录数
            max_workers: 并行工作线程的最大数量
            insert_method: 插入方法，可选值为'update'(更新),'ignore'(忽略重复),'direct'(直接插入)
            primary_keys: 主键列表，用于构建ON DUPLICATE KEY UPDATE语句，仅在insert_method='update'时有效
            callback: 可选的回调函数，处理每批次结果后调用，如果未提供则使用默认回调函数
            encrypted_columns: 需要加密的列名列表，这些列将使用TiDB的AES_ENCRYPT函数加密
            encryption_key: 加密密钥，默认为'petlibro123'
            max_retries: 最大重试次数，默认3次
            retry_backoff: 重试退避基数（秒），默认1.0
            max_backoff: 最大退避时间（秒），默认10.0
            
        返回:
            (插入记录数, 总耗时, 警告信息列表)
        """
        start_time = time.time()
        warnings = []
        
        # 如果未提供回调函数，使用默认回调
        if callback is None:
            callback = DataSyncUtils.default_batch_callback
        
        # 处理输入数据
        if isinstance(data, pd.DataFrame):
            # 如果是DataFrame，转换为字典列表
            if columns is None:
                columns = data.columns.tolist()
            
            # 处理NaN和None值
            for col in data.columns:
                data[col] = data[col].replace({pd.NA: None, float('nan'): None})
            
            # 转换为记录列表
            rows = []
            for _, row in data.iterrows():
                # 按列顺序提取值
                values = [row.get(col, None) for col in columns]
                rows.append(values)
        else:
            # 如果是字典列表
            if columns is None and data:
                # 从第一条记录推断列
                columns = list(data[0].keys())
            
            # 转换为记录列表
            rows = []
            for row in data:
                # 按列顺序提取值
                values = [row.get(col, None) for col in columns]
                rows.append(values)
        
        total_rows = len(rows)
        if total_rows == 0:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 没有数据需要写入")
            return 0, 0, warnings
        
        # 构建SQL语句
        table_name = db_config["table"]
        
        # 如果有加密列，需要特殊处理SQL构建
        if encrypted_columns:
            encrypted_columns_set = set(encrypted_columns)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 检测到加密列: {encrypted_columns}")
            
            # 构建列名和值的部分
            column_parts = []
            value_parts = []
            
            for col in columns:
                column_parts.append(f"`{col}`")
                if col in encrypted_columns_set:
                    # 对加密字段使用AES加密和Base64编码
                    value_parts.append(f"TO_BASE64(AES_ENCRYPT(%s, '{encryption_key}'))")
                else:
                    value_parts.append("%s")
            
            column_names = ', '.join(column_parts)
            placeholders = ', '.join(value_parts)
        else:
            # 普通模式，不加密
            column_names = ', '.join(['`' + col + '`' for col in columns])
            placeholders = ', '.join(['%s'] * len(columns))
        
        if insert_method == 'update':
            # 更新模式: INSERT ... ON DUPLICATE KEY UPDATE
            if not primary_keys:
                # 如果没有提供主键，假设第一列是主键
                primary_keys = [columns[0]]
            
            # 构建更新部分，排除主键字段
            update_columns = [col for col in columns if col not in primary_keys]
            
            if encrypted_columns:
                encrypted_columns_set = set(encrypted_columns)
                update_parts = []
                for col in update_columns:
                    if col in encrypted_columns_set:
                        # 对加密字段使用AES加密
                        update_parts.append(f"`{col}` = TO_BASE64(AES_ENCRYPT(VALUES(`{col}`), '{encryption_key}'))")
                    else:
                        update_parts.append(f"`{col}` = VALUES(`{col}`)")
                update_stmt = ', '.join(update_parts)
            else:
                update_stmt = ', '.join([f"`{col}` = VALUES(`{col}`)" for col in update_columns])
            
            insert_sql = f"""
                INSERT /*+ SET_VAR(tidb_dml_type='bulk') */ INTO {table_name} ({column_names})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE {update_stmt};
            """
        elif insert_method == 'ignore':
            # 忽略模式: INSERT IGNORE INTO
            insert_sql = f"""
                INSERT /*+ SET_VAR(tidb_dml_type='bulk') */ IGNORE INTO {table_name} ({column_names})
                VALUES ({placeholders});
            """
        else:
            # 直接插入模式: INSERT INTO
            insert_sql = f"""
                INSERT /*+ SET_VAR(tidb_dml_type='bulk') */ INTO {table_name} ({column_names})
                VALUES ({placeholders});
            """
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SQL: {insert_sql}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始并行写入数据到{db_config['table']}，总记录数: {total_rows}")
        
        # 分配数据到批次
        batches = []
        for i in range(0, total_rows, batch_size):
            end = min(i + batch_size, total_rows)
            batch_data = rows[i:end]
            batches.append(batch_data)
        
        # 限制工作线程数量
        actual_workers = min(max_workers, len(batches))
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 使用 {actual_workers} 个工作线程处理 {len(batches)} 个批次")
        
        # 使用ThreadPoolExecutor并行处理批次
        inserted_count = 0
        failed_batches = 0
        
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            # 提交所有批次任务（传递重试参数）
            future_to_batch = {
                executor.submit(
                    DataSyncUtils.batch_insert_worker, 
                    batch, 
                    insert_sql, 
                    db_config, 
                    i,
                    callback,
                    max_retries,
                    retry_backoff,
                    max_backoff
                ): i for i, batch in enumerate(batches)
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_batch):
                batch_id = future_to_batch[future]
                try:
                    data_count = future.result()
                    inserted_count += data_count
                    completion_percentage = inserted_count / total_rows * 100
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 进度: {inserted_count}/{total_rows} 条记录 ({completion_percentage:.1f}%)")
                except Exception as e:
                    failed_batches += 1
                    error_msg = f"批次 {batch_id} 处理失败: {str(traceback.format_exc())}"
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {error_msg}")
                    warnings.append(error_msg)
        
        total_time = time.time() - start_time
        rate = inserted_count / total_time if total_time > 0 else 0
        
        summary = (
            f"数据写入完成，共写入 {inserted_count}/{total_rows} 条记录，"
            f"失败批次: {failed_batches}，"
            f"总耗时: {total_time:.2f} 秒，"
            f"平均速度: {rate:.1f} 条/秒"
        )
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {summary}")
        
        return inserted_count, total_time, warnings
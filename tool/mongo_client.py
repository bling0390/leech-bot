from mongoengine import connect
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from beans.singleton import Singleton
from config.config import MONGO_HOST, MONGO_PORT, MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE_NAME
from typing import Optional
from loguru import logger

# 全局 Motor 客户端实例
motor_client: Optional[AsyncIOMotorClient] = None


def get_motor_client() -> AsyncIOMotorClient:
    """获取或创建 Motor 客户端实例"""
    global motor_client
    
    if motor_client is None:
        # 构建连接 URI
        if MONGO_USERNAME and MONGO_PASSWORD:
            uri = f'mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/'
        else:
            uri = f'mongodb://{MONGO_HOST}:{MONGO_PORT}/'
        
        motor_client = AsyncIOMotorClient(uri)
        logger.info(f"Motor 客户端已初始化，连接到: {MONGO_HOST}:{MONGO_PORT}")
    
    return motor_client


def get_collection(collection_name: str) -> AsyncIOMotorCollection:
    """
    获取 MongoDB 集合
    
    Args:
        collection_name: 集合名称
        
    Returns:
        AsyncIOMotorCollection: Motor 集合对象
        
    Raises:
        ValueError: 如果集合名称为空或 None
    """
    if collection_name is None:
        raise ValueError("Collection name cannot be None")
    
    if not collection_name or not collection_name.strip():
        raise ValueError("Collection name cannot be empty")
    
    client = get_motor_client()
    database = client[MONGO_DATABASE_NAME]
    collection = database[collection_name]
    
    return collection


class EstablishConnection(Singleton):
    def __init__(self):
        connect(
            db=MONGO_DATABASE_NAME,
            username=MONGO_USERNAME,
            password=MONGO_PASSWORD,
            host=f'mongodb://{MONGO_HOST}:{MONGO_PORT}/'
        )

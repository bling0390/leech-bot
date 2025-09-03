import os
import yaml
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger
import i18n
from beans.user_language import UserLanguage
from tool.mongo_client import get_motor_client
import time

# 数据库名称常量定义
# 使用环境变量支持不同部署环境的数据库配置
DATABASE_NAME = os.environ.get('MONGO_DATABASE', 'bot')

# 用户语言缓存 - 避免频繁查询和重复日志
_user_language_cache = {}
_cache_expire_seconds = 60  # 缓存1分钟
_cache_max_size = 1000  # 最大缓存条目数


class I18nManager:
    """国际化管理器"""
    
    def __init__(self):
        """初始化I18n管理器"""
        self.default_language = 'zh_CN'
        self.available_languages = ['zh_CN', 'en_US']
        self.translations = {}
        self.language_info = {
            'zh_CN': {
                'code': 'zh_CN',
                'name': 'Chinese (Simplified)',
                'native_name': '简体中文'
            },
            'en_US': {
                'code': 'en_US',
                'name': 'English',
                'native_name': 'English'
            }
        }
        
        # 初始化i18n
        self._setup_i18n()
        self._load_translations()
    
    def _setup_i18n(self):
        """配置i18n库"""
        # 设置语言文件路径
        locales_path = Path(__file__).parent.parent.parent.parent / 'locales'
        locales_path.mkdir(exist_ok=True)
        
        i18n.set('locale', self.default_language)
        i18n.set('fallback', self.default_language)
        i18n.set('filename_format', '{locale}.{format}')
        i18n.set('file_format', 'yml')
        i18n.set('enable_memoization', True)
        i18n.load_path.append(str(locales_path))
    
    def _load_translations(self):
        """加载所有语言的翻译文件"""
        locales_path = Path(__file__).parent.parent.parent.parent / 'locales'
        
        for lang in self.available_languages:
            file_path = locales_path / f"{lang}.yml"
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[lang] = yaml.safe_load(f) or {}
                    logger.info(f"加载语言文件: {lang}")
                except Exception as e:
                    logger.error(f"加载语言文件失败 {lang}: {e}")
                    self.translations[lang] = {}
            else:
                self.translations[lang] = {}
                logger.warning(f"语言文件不存在: {file_path}")
    
    def translate(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """
        翻译指定的key
        
        Args:
            key: 翻译key
            locale: 语言代码
            **kwargs: 翻译参数
            
        Returns:
            翻译后的文本
        """
        if locale not in self.available_languages:
            locale = self.default_language
        
        # 尝试从加载的翻译中获取
        translation = self._get_translation(key, locale)
        
        if translation is None:
            # 尝试从默认语言获取
            if locale != self.default_language:
                translation = self._get_translation(key, self.default_language)
            
            if translation is None:
                # 返回key本身作为最后的回退
                return key
        
        # 处理参数替换
        if kwargs:
            try:
                # 处理复数形式
                if 'count' in kwargs and isinstance(translation, dict):
                    count = kwargs['count']
                    if count == 1 and 'one' in translation:
                        translation = translation['one']
                    elif 'other' in translation:
                        translation = translation['other']
                    else:
                        # 如果没有合适的复数形式，使用第一个可用的值
                        translation = list(translation.values())[0]
                
                # 格式化字符串（只在translation是字符串时）
                if isinstance(translation, str):
                    translation = translation.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(f"翻译参数替换失败: {e}")
        
        return str(translation)
    
    def _get_translation(self, key: str, locale: str) -> Optional[Any]:
        """
        从翻译字典中获取翻译
        
        Args:
            key: 翻译key（支持点分隔的嵌套key）
            locale: 语言代码
            
        Returns:
            翻译文本、字典或None
        """
        if locale not in self.translations:
            return None
        
        # 处理嵌套的key
        keys = key.split('.')
        value = self.translations[locale]
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    async def translate_for_user(self, user_id: int, key: str, **kwargs) -> str:
        """
        根据用户偏好的语言进行翻译
        
        Args:
            user_id: 用户ID
            key: 翻译key
            **kwargs: 翻译参数
            
        Returns:
            翻译后的文本
        """
        language = await get_user_language(user_id)
        return self.translate(key, locale=language, **kwargs)
    
    def get_available_languages(self) -> List[Dict[str, str]]:
        """
        获取可用语言列表
        
        Returns:
            语言信息列表
        """
        return list(self.language_info.values())
    
    def set_user_language(self, user_id: int, language: str) -> bool:
        """
        设置用户语言
        
        Args:
            user_id: 用户ID
            language: 语言代码
            
        Returns:
            是否设置成功
        """
        if language not in self.available_languages:
            return False
        
        try:
            return save_user_language(user_id, language)
        except Exception as e:
            logger.error(f"设置用户语言失败: {e}")
            return False
    
    def reload_translations(self):
        """重新加载翻译文件"""
        self._load_translations()
        logger.info("翻译文件已重新加载")
    
    def is_language_loaded(self, language: str) -> bool:
        """
        检查语言是否已加载
        
        Args:
            language: 语言代码
            
        Returns:
            是否已加载
        """
        return language in self.translations and bool(self.translations[language])
    
    def format_message(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """
        格式化消息（支持HTML）
        
        Args:
            key: 翻译key
            locale: 语言代码
            **kwargs: 翻译参数
            
        Returns:
            格式化后的消息
        """
        message = self.translate(key, locale=locale, **kwargs)
        
        # 这里可以添加HTML格式化逻辑
        if '<b>' not in message and '<i>' not in message:
            # 如果消息中没有HTML标签，自动添加一些基本格式
            if key.startswith('disk.alert'):
                message = f"<b>{message}</b>"
        
        return message
    
    async def get_user_language(self, user_id: int) -> str:
        """
        获取用户语言偏好
        
        Args:
            user_id: 用户ID
            
        Returns:
            语言代码
        """
        return await get_user_language(user_id)
    
    async def save_user_language(self, user_id: int, language: str) -> bool:
        """
        保存用户语言偏好
        
        Args:
            user_id: 用户ID
            language: 语言代码
            
        Returns:
            是否保存成功
        """
        if language not in self.available_languages:
            return False
        
        return await save_user_language_async(user_id, language)
    
    async def translate_async(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """
        异步翻译（用于并发场景）
        
        Args:
            key: 翻译key
            locale: 语言代码
            **kwargs: 翻译参数
            
        Returns:
            翻译后的文本
        """
        # 在异步环境中执行翻译
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.translate, 
            key, 
            locale, 
            kwargs
        )


def _clean_cache():
    """清理过期和过多的缓存条目"""
    current_time = time.time()
    
    # 清理过期条目
    expired_keys = [
        key for key, entry in _user_language_cache.items()
        if current_time - entry['timestamp'] > _cache_expire_seconds
    ]
    for key in expired_keys:
        del _user_language_cache[key]
    
    # 如果缓存过大，清理最旧的条目
    if len(_user_language_cache) > _cache_max_size:
        sorted_entries = sorted(
            _user_language_cache.items(),
            key=lambda x: x[1]['timestamp']
        )
        # 删除最旧的条目，保留最新的 _cache_max_size 条
        for key, _ in sorted_entries[:-_cache_max_size]:
            del _user_language_cache[key]


async def get_user_language(user_id: int) -> str:
    """
    获取用户的语言设置（带缓存优化）
    
    Args:
        user_id: 用户ID
        
    Returns:
        语言代码
    """
    current_time = time.time()
    cache_key = f"user_lang_{user_id}"
    
    # 检查缓存
    if cache_key in _user_language_cache:
        cache_entry = _user_language_cache[cache_key]
        if current_time - cache_entry['timestamp'] < _cache_expire_seconds:
            # 缓存有效，直接返回（不产生额外日志）
            return cache_entry['language']
    
    # 定期清理缓存（低概率触发）
    if len(_user_language_cache) > _cache_max_size * 0.8:
        _clean_cache()
    
    try:
        # 优先从同步方法获取（使用本地缓存或快速访问）
        user_lang = UserLanguage.get_user_language(user_id)
        if user_lang:
            logger.debug(f"获取用户 {user_id} 语言: {user_lang}")
            # 更新缓存
            _user_language_cache[cache_key] = {
                'language': user_lang,
                'timestamp': current_time
            }
            return user_lang
            
        # 如果同步方法失败，从异步MongoDB直接获取
        client = get_motor_client()
        db = client[DATABASE_NAME]
        collection = db['user_language']
        
        result = await collection.find_one({'user_id': user_id})
        if result:
            language_code = result.get('language_code', result.get('language', 'zh_CN'))
            logger.debug(f"从数据库获取用户 {user_id} 语言: {language_code}")
            # 更新缓存
            _user_language_cache[cache_key] = {
                'language': language_code,
                'timestamp': current_time
            }
            return language_code
            
    except Exception as e:
        logger.error(f"获取用户 {user_id} 语言失败: {e}")
    
    # 返回默认语言并记录
    default_lang = 'zh_CN'
    logger.info(f"用户 {user_id} 使用默认语言: {default_lang}")
    # 缓存默认语言（较短时间）
    _user_language_cache[cache_key] = {
        'language': default_lang,
        'timestamp': current_time
    }
    return default_lang


def save_user_language(user_id: int, language: str) -> bool:
    """
    保存用户的语言设置（同步版本）
    
    Args:
        user_id: 用户ID
        language: 语言代码
        
    Returns:
        是否保存成功
    """
    if not language or not isinstance(user_id, int):
        logger.warning(f"无效的输入参数 - 用户ID: {user_id}, 语言: {language}")
        return False
    
    try:
        result = UserLanguage.set_user_language(user_id, language)
        if result:
            logger.info(f"同步保存用户 {user_id} 语言偏好为: {language}")
            # 清除缓存，确保下次获取最新数据
            cache_key = f"user_lang_{user_id}"
            if cache_key in _user_language_cache:
                del _user_language_cache[cache_key]
        return result
    except Exception as e:
        logger.error(f"同步保存用户 {user_id} 语言 {language} 失败: {e}")
        return False


async def save_user_language_async(user_id: int, language: str) -> bool:
    """
    保存用户的语言设置（异步版本）
    
    Args:
        user_id: 用户ID
        language: 语言代码
        
    Returns:
        是否保存成功
    """
    if not language or not isinstance(user_id, int):
        logger.warning(f"无效的输入参数 - 用户ID: {user_id}, 语言: {language}")
        return False
    
    try:
        # 使用Motor客户端进行异步操作
        client = get_motor_client()
        db = client[DATABASE_NAME]
        collection = db['user_language']
        
        # 添加创建和更新时间戳
        from datetime import datetime
        now = datetime.utcnow()
        
        result = await collection.update_one(
            {'user_id': user_id},
            {
                '$set': {
                    'user_id': user_id, 
                    'language_code': language,
                    'updated_at': now
                },
                '$setOnInsert': {
                    'created_at': now
                }
            },
            upsert=True
        )
        
        success = result.modified_count > 0 or result.upserted_id is not None
        
        if success:
            logger.info(f"成功保存用户 {user_id} 语言偏好为: {language}")
            # 清除缓存，确保下次获取最新数据
            cache_key = f"user_lang_{user_id}"
            if cache_key in _user_language_cache:
                del _user_language_cache[cache_key]
        else:
            logger.warning(f"用户 {user_id} 语言偏好保存操作未产生变化")
            
        return success
        
    except Exception as e:
        logger.error(f"异步保存用户 {user_id} 语言 {language} 失败: {e}")
        return False


async def get_motor_collection(collection_name: str):
    """
    获取Motor集合
    
    Args:
        collection_name: 集合名称
        
    Returns:
        Motor集合对象
    """
    client = get_motor_client()
    db = client[DATABASE_NAME]
    return db[collection_name]


def get_cache_stats() -> Dict[str, Any]:
    """
    获取缓存统计信息
    
    Returns:
        缓存统计字典
    """
    current_time = time.time()
    active_entries = 0
    expired_entries = 0
    
    for entry in _user_language_cache.values():
        if current_time - entry['timestamp'] < _cache_expire_seconds:
            active_entries += 1
        else:
            expired_entries += 1
    
    return {
        'total_entries': len(_user_language_cache),
        'active_entries': active_entries,
        'expired_entries': expired_entries,
        'cache_hit_ratio': f"{(active_entries / max(len(_user_language_cache), 1)) * 100:.1f}%",
        'cache_expire_seconds': _cache_expire_seconds,
        'cache_max_size': _cache_max_size
    }


def clear_user_language_cache():
    """
    清空用户语言缓存
    """
    global _user_language_cache
    _user_language_cache = {}
    logger.info("用户语言缓存已清空")
"""
User language preference model for MongoDB
"""
from mongoengine import Document, StringField, IntField, DateTimeField
from datetime import datetime


class UserLanguage(Document):
    """MongoDB model for storing user language preferences"""
    
    # User ID (Telegram user ID)
    user_id = IntField(required=True, unique=True)
    
    # Language code (e.g., 'zh_CN', 'en_US')
    language_code = StringField(required=True, default='zh_CN')
    
    # Created timestamp
    created_at = DateTimeField(default=datetime.utcnow)
    
    # Updated timestamp
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'user_language',
        'indexes': [
            'user_id',
            'language_code'
        ]
    }
    
    def save(self, *args, **kwargs):
        """Override save to update timestamp"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_user_language(cls, user_id: int) -> str:
        """
        Get user's language preference
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Language code (defaults to 'zh_CN' if not found)
        """
        if not isinstance(user_id, int) or user_id <= 0:
            from loguru import logger
            logger.warning(f"无效的用户ID: {user_id}")
            return 'zh_CN'
            
        try:
            user_lang = cls.objects(user_id=user_id).first()
            if user_lang:
                return user_lang.language_code
            else:
                # 用户第一次使用，返回默认语言
                return 'zh_CN'
        except Exception as e:
            from loguru import logger
            logger.error(f"获取用户 {user_id} 语言偏好时发生错误: {e}")
            return 'zh_CN'
    
    @classmethod
    def set_user_language(cls, user_id: int, language_code: str) -> bool:
        """
        Set or update user's language preference
        
        Args:
            user_id: Telegram user ID
            language_code: Language code to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user_lang = cls.objects(user_id=user_id).first()
            if user_lang:
                user_lang.language_code = language_code
                user_lang.save()
            else:
                new_user_lang = cls(user_id=user_id, language_code=language_code)
                new_user_lang.save()
            return True
        except Exception as e:
            # 改进错误处理，记录具体错误信息
            from loguru import logger
            logger.error(f"设置用户语言失败 - 用户ID: {user_id}, 语言: {language_code}, 错误: {e}")
            return False
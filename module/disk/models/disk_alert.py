from datetime import datetime
from mongoengine import Document, StringField, FloatField, DateTimeField, IntField


class DiskAlert(Document):
    """磁盘告警MongoDB模型"""
    
    meta = {
        'collection': 'monitor',  # 使用monitor表
        'indexes': [
            'timestamp',
            'alert_status',
            '-timestamp'  # 降序索引用于查询最新记录
        ]
    }
    
    # 告警基本信息
    timestamp = DateTimeField(required=True, default=datetime.now)
    free_space_gb = FloatField(required=True)
    used_percent = FloatField(required=True)
    total_gb = FloatField()
    used_gb = FloatField()
    threshold_gb = FloatField(required=True)
    location = StringField(default='/downloads')
    
    # 告警消息和状态
    alert_message = StringField(required=True)
    alert_status = StringField(
        required=True,
        choices=['active', 'resolved', 'ignored'],
        default='active'
    )
    
    # 处理信息
    action_taken = StringField(choices=[
        'cleaned_downloads',
        'adjusted_celery',
        'manual_cleanup',
        'ignored',
        None
    ])
    resolved_at = DateTimeField()
    resolved_by = IntField()  # Telegram用户ID
    
    # 额外信息
    freed_space_gb = FloatField()  # 清理后释放的空间
    celery_adjustment = StringField()  # Celery调整详情
    notes = StringField()  # 备注
    
    def __str__(self):
        return f"DiskAlert({self.timestamp}, {self.free_space_gb}GB free, {self.alert_status})"
    
    @classmethod
    def get_active_alerts(cls):
        """获取所有活跃的告警"""
        return cls.objects(alert_status='active').order_by('-timestamp')
    
    @classmethod
    def get_recent_alerts(cls, hours=24):
        """获取最近N小时的告警"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return cls.objects(timestamp__gte=cutoff_time).order_by('-timestamp')
    
    def resolve(self, action: str, user_id: int = None, notes: str = None):
        """解决告警
        
        Args:
            action: 采取的动作
            user_id: 处理用户ID
            notes: 备注
        """
        self.alert_status = 'resolved'
        self.action_taken = action
        self.resolved_at = datetime.now()
        if user_id:
            self.resolved_by = user_id
        if notes:
            self.notes = notes
        self.save()
        
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': str(self.id),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'free_space_gb': self.free_space_gb,
            'used_percent': self.used_percent,
            'threshold_gb': self.threshold_gb,
            'alert_status': self.alert_status,
            'action_taken': self.action_taken,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
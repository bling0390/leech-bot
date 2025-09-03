"""
磁盘监控配置验证模块
"""

from typing import Dict, Any
from module.i18n import get_i18n_manager


def validate_disk_monitor_config(config: Dict[str, Any], locale: str = 'zh_CN') -> Dict[str, Any]:
    """验证磁盘监控配置
    
    Args:
        config: 配置字典
        locale: 语言代码
        
    Returns:
        包含验证结果的字典
    """
    i18n = get_i18n_manager()
    errors = []
    warnings = []
    
    # 验证阈值
    threshold = config.get('DISK_ALERT_THRESHOLD')
    if threshold is not None:
        try:
            threshold_val = int(threshold)
            if threshold_val <= 0:
                errors.append(i18n.translate('disk.config.validation.threshold_required', locale=locale))
            elif threshold_val < 1:
                warnings.append(i18n.translate('disk.config.validation.threshold_too_small', locale=locale))
            elif threshold_val > 100:
                warnings.append(i18n.translate('disk.config.validation.threshold_too_large', locale=locale))
        except (ValueError, TypeError):
            errors.append(i18n.translate('disk.config.validation.threshold_invalid', locale=locale))
    
    # 验证启用状态
    enabled = config.get('DISK_ALERT_ENABLED')
    if enabled is not None:
        if not isinstance(enabled, bool) and enabled not in ['true', 'false', True, False]:
            errors.append(i18n.translate('disk.config.validation.enabled_invalid', locale=locale))
    
    # 验证自动启动状态
    auto_start = config.get('DISK_MONITOR_AUTO_START')
    if auto_start is not None:
        if not isinstance(auto_start, bool) and auto_start not in ['true', 'false', True, False]:
            errors.append(i18n.translate('disk.config.validation.auto_start_invalid', locale=locale))
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }
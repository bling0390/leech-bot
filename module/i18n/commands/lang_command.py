from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ParseMode
from loguru import logger
from tool.utils import is_admin
from module.i18n import get_i18n_manager


@Client.on_message(filters.command('lang') & filters.private & is_admin)
async def lang_command(client: Client, message: Message):
    """语言设置命令"""
    try:
        user_id = message.from_user.id
        i18n = get_i18n_manager()
        
        # 获取用户当前语言
        current_lang = await i18n.get_user_language(user_id)
        available_languages = i18n.get_available_languages()
        
        # 找到当前语言的显示名称
        current_lang_info = next(
            (lang for lang in available_languages if lang['code'] == current_lang), 
            {'native_name': current_lang}
        )
        
        # 构建消息
        menu_title = await i18n.translate_for_user(user_id, 'language.menu_title')
        select_prompt = await i18n.translate_for_user(user_id, 'language.select_prompt')
        current_text = await i18n.translate_for_user(
            user_id, 
            'language.current',
            language=current_lang_info['native_name']
        )
        
        message_text = (
            f"{menu_title}\n\n"
            f"{current_text}\n\n"
            f"{select_prompt}"
        )
        
        # 创建语言选择按钮
        keyboard = create_language_keyboard(available_languages, current_lang)
        
        await message.reply_text(
            message_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"语言命令处理失败: {e}")
        await message.reply_text("❌ 处理命令时发生错误")


def create_language_keyboard(languages, current_lang):
    """创建语言选择键盘"""
    buttons = []
    
    for lang in languages:
        # 标记当前选中的语言
        text = f"{'✅ ' if lang['code'] == current_lang else ''}{lang['native_name']}"
        callback_data = f"lang_{lang['code']}"
        
        buttons.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    # 添加关闭按钮
    buttons.append([InlineKeyboardButton("❌ 关闭", callback_data="lang_close")])
    
    return InlineKeyboardMarkup(buttons)


@Client.on_callback_query(filters.regex(r'^lang_'))
async def handle_lang_callback(client: Client, callback_query: CallbackQuery):
    """处理语言选择回调"""
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data
        i18n = get_i18n_manager()
        
        if data == "lang_close":
            # 关闭菜单
            await callback_query.message.delete()
            await callback_query.answer()
            return
        
        # 提取语言代码
        lang_code = data.replace("lang_", "")
        
        # 验证语言代码
        available_languages = i18n.get_available_languages()
        valid_codes = [lang['code'] for lang in available_languages]
        
        if lang_code not in valid_codes:
            error_msg = await i18n.translate_for_user(
                user_id, 
                'language.invalid',
                language=lang_code
            )
            await callback_query.answer(error_msg, show_alert=True)
            return
        
        # 保存用户语言设置
        logger.info(f"用户 {user_id} 尝试切换语言为: {lang_code}")
        success = await i18n.save_user_language(user_id, lang_code)
        
        if success:
            # 获取新语言的显示名称
            lang_info = next(
                (lang for lang in available_languages if lang['code'] == lang_code),
                {'native_name': lang_code}
            )
            
            success_msg = await i18n.translate_for_user(
                user_id,
                'language.changed',
                language=lang_info['native_name']
            )
            
            # 删除原消息
            await callback_query.message.delete()
            await callback_query.answer(success_msg, show_alert=False)
            
            logger.success(f"✅ 用户 {user_id} 成功切换语言为: {lang_code} ({lang_info['native_name']})")
        else:
            error_msg = await i18n.translate_for_user(
                user_id,
                'language.save_failed',
                language=lang_code
            )
            await callback_query.answer(error_msg, show_alert=True)
            logger.error(f"❌ 用户 {user_id} 语言切换失败: {lang_code}")
            
    except Exception as e:
        logger.error(f"语言切换回调处理失败: {e}")
        await callback_query.answer("❌ 操作失败", show_alert=True)


# 为了向后兼容，也注册一个语言状态查询命令
@Client.on_message(filters.command('lang_status') & filters.private & is_admin)
async def lang_status(client: Client, message: Message):
    """查看当前语言状态"""
    try:
        user_id = message.from_user.id
        i18n = get_i18n_manager()
        
        current_lang = await i18n.get_user_language(user_id)
        available_languages = i18n.get_available_languages()
        
        # 找到当前语言信息
        current_lang_info = next(
            (lang for lang in available_languages if lang['code'] == current_lang),
            {'code': current_lang, 'name': current_lang, 'native_name': current_lang}
        )
        
        current_text = await i18n.translate_for_user(
            user_id,
            'language.current',
            language=current_lang_info['native_name']
        )
        
        # 构建状态信息
        status_text = (
            f"🌐 <b>语言设置状态</b>\n\n"
            f"{current_text}\n"
            f"语言代码: <code>{current_lang}</code>\n"
            f"英文名称: {current_lang_info['name']}\n\n"
            f"使用 <code>/lang</code> 命令切换语言"
        )
        
        await message.reply_text(status_text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"语言状态查询失败: {e}")
        await message.reply_text("❌ 查询失败")
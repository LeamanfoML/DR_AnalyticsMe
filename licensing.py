import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import AsyncDatabase
from config import config
import re

# Настройка логирования
logger = logging.getLogger(__name__)
router = Router()

class LicenseActivation(StatesGroup):
    AWAITING_KEY = State()

class LicenseManager:
    def __init__(self, db: AsyncDatabase):
        self.db = db
        logger.info("LicenseManager initialized")

    async def check_license(self, user_id: int) -> bool:
        """Проверка наличия активной лицензии"""
        try:
            # Проверка администратора
            if user_id == config.ADMIN_CHAT_ID:
                return True
                
            # Проверка в базе данных
            license = await self.get_license(user_id)
            return license and license['is_active']
        except Exception as e:
            logger.error(f"License check error: {e}")
            return False

    async def get_license(self, user_id: int):
        """Получение информации о лицензии"""
        # В реальной реализации здесь будет запрос к базе
        # Для примера возвращаем фиктивные данные
        return {
            'user_id': user_id,
            'license_key': 'XXXX-XXXX-XXXX-XXXX',
            'is_active': True,
            'expiry_date': '2024-12-31'
        }

    async def activate_license(self, user_id: int, license_key: str) -> bool:
        """Активация лицензии"""
        if not self._validate_key_format(license_key):
            return False
            
        # Здесь должна быть реальная проверка ключа через API
        is_valid = await self._validate_key(license_key)
        
        if is_valid:
            # В реальной реализации здесь сохранение в базу
            logger.info(f"License activated for {user_id}")
            return True
        return False

    def _validate_key_format(self, key: str) -> bool:
        """Проверка формата ключа"""
        pattern = r"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"
        return re.match(pattern, key) is not None

    async def _validate_key(self, key: str) -> bool:
        """Реальная валидация ключа (заглушка)"""
        # В реальном приложении здесь запрос к лицензионному серверу
        await asyncio.sleep(1)  # Имитация сетевого запроса
        return True

# Инициализация менеджера лицензий (будет в основном файле)
# db = AsyncDatabase(config.DB_PATH)
# license_manager = LicenseManager(db)

@router.message(Command("license"))
async def license_command(message: Message, license_manager: LicenseManager):
    """Обработка команды /license"""
    try:
        user_id = message.from_user.id
        
        if await license_manager.check_license(user_id):
            license_info = await license_manager.get_license(user_id)
            text = (
                "🔐 *Ваша лицензия активна!*\n\n"
                f"• Ключ: `{license_info['license_key']}`\n"
                f"• Действует до: `{license_info['expiry_date']}`\n\n"
                "Для управления используйте /license_menu"
            )
        else:
            text = (
                "⚠️ *Лицензия не активирована*\n\n"
                "Для использования бота необходимо активировать лицензию. "
                "Отправьте лицензионный ключ командой:\n"
                "/activate <ваш_ключ>\n\n"
                "Или используйте меню: /license_menu"
            )
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"License command error: {e}")
        await message.answer("⚠️ Ошибка обработки запроса лицензии")

@router.message(Command("activate"))
async def activate_license_cmd(message: Message, license_manager: LicenseManager, state: FSMContext):
    """Активация лицензии по ключу"""
    try:
        user_id = message.from_user.id
        license_key = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        
        if not license_key:
            await message.answer("ℹ️ Использование: /activate <лицензионный_ключ>")
            return
            
        success = await license_manager.activate_license(user_id, license_key)
        
        if success:
            await message.answer("✅ *Лицензия успешно активирована!*\n\nТеперь вы можете использовать все функции бота.", 
                               parse_mode="Markdown")
        else:
            await message.answer("❌ *Неверный лицензионный ключ*\n\nПроверьте правильность ключа и попробуйте снова.",
                               parse_mode="Markdown")
                               
    except Exception as e:
        logger.error(f"License activation error: {e}")
        await message.answer("⚠️ Ошибка активации лицензии")

@router.message(Command("license_menu"))
async def license_menu(message: Message, license_manager: LicenseManager):
    """Меню управления лицензией"""
    try:
        user_id = message.from_user.id
        has_license = await license_manager.check_license(user_id)
        
        text = "🔐 *Управление лицензией*"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        if has_license:
            license_info = await license_manager.get_license(user_id)
            text += (
                f"\n\n• Статус: `Активна`\n"
                f"• Ключ: `{license_info['license_key'][:8]}...`\n"
                f"• Истекает: `{license_info['expiry_date']}`"
            )
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text="🔄 Продлить лицензию", callback_data="renew_license")]
            )
        else:
            text += "\n\nℹ️ У вас нет активной лицензии"
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text="🔑 Активировать ключ", callback_data="activate_license")]
            )
            
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="ℹ️ Информация", callback_data="license_info")]
        )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        )
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"License menu error: {e}")
        await message.answer("⚠️ Ошибка загрузки меню лицензии")

@router.callback_query(F.data == "activate_license")
async def activate_license_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка активации лицензии через меню"""
    try:
        await state.set_state(LicenseActivation.AWAITING_KEY)
        await callback.message.answer("✏️ Введите ваш лицензионный ключ:")
        await callback.answer()
    except Exception as e:
        logger.error(f"License activation callback error: {e}")
        await callback.message.answer("⚠️ Ошибка обработки запроса")

@router.message(LicenseActivation.AWAITING_KEY)
async def process_license_key(message: Message, state: FSMContext, license_manager: LicenseManager):
    """Обработка введенного лицензионного ключа"""
    try:
        user_id = message.from_user.id
        license_key = message.text.strip()
        
        success = await license_manager.activate_license(user_id, license_key)
        
        if success:
            await message.answer("✅ *Лицензия успешно активирована!*", parse_mode="Markdown")
        else:
            await message.answer("❌ *Неверный лицензионный ключ*\nПопробуйте снова или введите /cancel")
        
        await state.clear()
    except Exception as e:
        logger.error(f"License key processing error: {e}")
        await message.answer("⚠️ Ошибка обработки ключа")
        await state.clear()

@router.callback_query(F.data == "renew_license")
async def renew_license(callback: CallbackQuery):
    """Продление лицензии"""
    try:
        # Здесь будет логика продления лицензии
        await callback.message.answer("ℹ️ Функция продления лицензии в разработке")
        await callback.answer()
    except Exception as e:
        logger.error(f"License renewal error: {e}")
        await callback.message.answer("⚠️ Ошибка продления лицензии")

@router.callback_query(F.data == "license_info")
async def license_info(callback: CallbackQuery):
    """Информация о лицензии"""
    try:
        text = (
            "📜 *Информация о лицензии*\n\n"
            "• Лицензия предоставляет доступ ко всем функциям бота\n"
            "• Один ключ активируется только на одного пользователя\n"
            "• При смене устройства необходима повторная активация\n\n"
            "По вопросам приобретения лицензии обращайтесь к @администратор"
        )
        await callback.message.answer(text, parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.error(f"License info error: {e}")
        await callback.message.answer("⚠️ Ошибка загрузки информации")

from aiohttp import web
import aiohttp_jinja2
import jinja2
from pathlib import Path
from database import AsyncDatabase
from config import config
import logging
import json
import asyncio

# Настройка логирования
logger = logging.getLogger('web_interface')

class WebServer:
    def __init__(self, db: AsyncDatabase):
        self.db = db
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.setup_routes()
        self.setup_templates()
        logger.info("WebServer initialized")

    def setup_templates(self):
        """Настройка шаблонизатора Jinja2"""
        templates_path = Path(__file__).parent / 'templates'
        aiohttp_jinja2.setup(
            self.app,
            loader=jinja2.FileSystemLoader(str(templates_path))
        
        # Добавляем глобальные фильтры
        env = aiohttp_jinja2.get_env(self.app)
        env.filters['format_float'] = lambda x: f"{x:.4f}"
        env.filters['format_datetime'] = lambda dt: dt.strftime("%d.%m.%Y %H:%M") if dt else ""

    def setup_routes(self):
        """Настройка маршрутов веб-сервера"""
        self.app.add_routes([
            web.get('/', self.index),
            web.get('/settings', self.get_settings),
            web.post('/settings', self.update_settings),
            web.get('/deals', self.get_deals),
            web.get('/status', self.get_status),
            web.static('/static', Path(__file__).parent / 'static')
        ])
    
    @aiohttp_jinja2.template('index.html')
    async def index(self, request):
        """Главная страница"""
        settings = await self.db.get_settings()
        last_deals = await self.db.get_deals(limit=5)
        return {
            'settings': settings,
            'deals': last_deals,
            'title': 'Arbitrage Bot Dashboard'
        }
    
    @aiohttp_jinja2.template('settings.html')
    async def get_settings(self, request):
        """Получение настроек"""
        settings = await self.db.get_settings()
        return {'settings': settings}
    
    async def update_settings(self, request):
        """Обновление настроек"""
        try:
            data = await request.json()
            logger.info(f"Updating settings: {data}")
            
            # Преобразование значений
            for key in data:
                if key in ['tonnel_enabled', 'portals_enabled']:
                    data[key] = int(data[key])
                else:
                    data[key] = float(data[key])
            
            success = await self.db.update_settings(data)
            if success:
                return web.json_response({'status': 'success'})
            return web.json_response({'status': 'error', 'message': 'Database error'}, status=500)
        
        except json.JSONDecodeError:
            return web.json_response({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    @aiohttp_jinja2.template('deals.html')
    async def get_deals(self, request):
        """Получение истории сделок"""
        limit = int(request.query.get('limit', 50))
        deals = await self.db.get_deals(limit=limit)
        return {'deals': deals, 'title': 'Deal History'}
    
    async def get_status(self, request):
        """Проверка статуса сервера"""
        return web.json_response({
            'status': 'running',
            'database': 'connected' if self.db else 'disconnected'
        })
    
    async def start(self):
        """Запуск веб-сервера"""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(
            self.runner, 
            config.WEB_SERVER_HOST, 
            config.WEB_SERVER_PORT
        )
        
        await self.site.start()
        logger.info(f"Web server started at http://{config.WEB_SERVER_HOST}:{config.WEB_SERVER_PORT}")
    
    async def stop(self):
        """Остановка веб-сервера"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Web server stopped")

async def start_web_server(db: AsyncDatabase):
    """Создание и запуск веб-сервера"""
    server = WebServer(db)
    await server.start()
    return server

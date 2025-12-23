"""
Планировщик автоматического обновления справочников ЦБ РФ
Запускается ежедневно для актуализации BANK_REGISTRY
"""

import schedule
import time
import threading
from datetime import datetime
from pathlib import Path
import json
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cbr_updates.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BankRegistryUpdater:
    """Класс для автоматического обновления реестра банков"""
    
    def __init__(self):
        self.last_update_file = Path("cbr_data") / "last_update.json"
        self.bank_registry_file = Path("cbr_data") / "bank_registry.json"
        self.mfo_registry_file = Path("cbr_data") / "mfo_registry.json"
        self.is_running = False
        self.update_thread = None
    
    def get_last_update_info(self) -> dict:
        """Получить информацию о последнем обновлении"""
        if self.last_update_file.exists():
            try:
                with open(self.last_update_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "last_update": None,
            "next_update": None,
            "banks_count": 0,
            "updated_count": 0,
            "status": "never_updated"
        }
    
    def save_update_info(self, info: dict):
        """Сохранить информацию об обновлении"""
        self.last_update_file.parent.mkdir(exist_ok=True)
        with open(self.last_update_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
    
    def save_registries(self):
        """Сохранить реестры банков и МФО в файлы"""
        from processor import DocumentProcessor
        
        self.bank_registry_file.parent.mkdir(exist_ok=True)
        
        # Сохраняем BANK_REGISTRY
        with open(self.bank_registry_file, 'w', encoding='utf-8') as f:
            json.dump(DocumentProcessor.BANK_REGISTRY, f, ensure_ascii=False, indent=2)
        
        # Сохраняем MFO_REGISTRY
        with open(self.mfo_registry_file, 'w', encoding='utf-8') as f:
            json.dump(DocumentProcessor.MFO_REGISTRY, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[SAVE] Реестры сохранены: {len(DocumentProcessor.BANK_REGISTRY)} банков, {len(DocumentProcessor.MFO_REGISTRY)} МФО")
    
    def load_registries(self):
        """Загрузить реестры банков и МФО из файлов"""
        from processor import DocumentProcessor
        
        loaded_banks = 0
        loaded_mfo = 0
        
        # Загружаем BANK_REGISTRY
        if self.bank_registry_file.exists():
            try:
                with open(self.bank_registry_file, 'r', encoding='utf-8') as f:
                    DocumentProcessor.BANK_REGISTRY = json.load(f)
                    loaded_banks = len(DocumentProcessor.BANK_REGISTRY)
                    logger.info(f"[LOAD] Загружено банков из файла: {loaded_banks}")
            except Exception as e:
                logger.error(f"[ERROR] Ошибка загрузки BANK_REGISTRY: {e}")
        
        # Загружаем MFO_REGISTRY
        if self.mfo_registry_file.exists():
            try:
                with open(self.mfo_registry_file, 'r', encoding='utf-8') as f:
                    DocumentProcessor.MFO_REGISTRY = json.load(f)
                    loaded_mfo = len(DocumentProcessor.MFO_REGISTRY)
                    logger.info(f"[LOAD] Загружено МФО из файла: {loaded_mfo}")
            except Exception as e:
                logger.error(f"[ERROR] Ошибка загрузки MFO_REGISTRY: {e}")
        
        return loaded_banks, loaded_mfo
    
    def update_registry(self):
        """Выполнить обновление реестра банков и МФО"""
        from cbr_registry import CBRExcelRegistry
        from processor import DocumentProcessor
        
        logger.info("[UPDATE] Начинаю обновление реестра банков и МФО...")
        
        try:
            # Создаем объект для работы с ЦБ
            cbr_registry = CBRExcelRegistry()
            
            # === ОБНОВЛЕНИЕ БАНКОВ ===
            # Скачиваем актуальный справочник банков
            logger.info("[DOWNLOAD] Скачиваю справочник банков ЦБ РФ...")
            banks_file = cbr_registry.download_banks_registry()
            
            if not banks_file or not banks_file.exists():
                logger.error("[ERROR] Не удалось скачать справочник банков")
                return False
            
            # Парсим справочник банков
            logger.info("[PARSE] Парсю справочник банков...")
            banks_data = cbr_registry.parse_banks_registry(banks_file)
            
            if not banks_data:
                logger.error("[ERROR] Не удалось распарсить справочник банков")
                return False
            
            logger.info(f"[OK] Загружено банков: {len(banks_data)}")
            
            # Получаем текущий BANK_REGISTRY из processor.py
            current_registry = DocumentProcessor.BANK_REGISTRY.copy()
            
            # Обновляем реестр банков (добавляем все из XLSX + нормализуем названия)
            logger.info("[UPDATE] Обновляю реестр банков из XLSX...")
            updated_registry = cbr_registry.update_bank_registry_addresses(
                current_registry, 
                banks_data
            )
            
            # Подсчитываем изменения
            added_count = len(updated_registry) - len(current_registry)
            updated_count = sum(
                1 for inn in current_registry.keys()
                if inn in updated_registry and (
                    current_registry[inn]['адрес'] != updated_registry[inn]['адрес'] or
                    current_registry[inn]['название'] != updated_registry[inn]['название']
                )
            )
            
            # Обновляем BANK_REGISTRY в памяти
            DocumentProcessor.BANK_REGISTRY = updated_registry
            logger.info(f"[OK] Реестр банков обновлен: {len(updated_registry)} банков (добавлено: {added_count}, обновлено: {updated_count})")
            
            # === ОБНОВЛЕНИЕ МФО ===
            # Скачиваем актуальный справочник МФО
            logger.info("[DOWNLOAD] Скачиваю справочник МФО...")
            mfo_file = cbr_registry.download_mfo_registry()
            
            if not mfo_file or not mfo_file.exists():
                logger.warning("[WARNING] Не удалось скачать справочник МФО")
                mfo_data = []
            else:
                # Парсим справочник МФО
                logger.info("[PARSE] Парсю справочник МФО...")
                mfo_data = cbr_registry.parse_mfo_registry(mfo_file)
                logger.info(f"[OK] Загружено МФО: {len(mfo_data)}")
            
            # Заполняем MFO_REGISTRY из XLSX
            mfo_registry = {}
            for mfo in mfo_data:
                inn = mfo.get('Идентификационный номер налогоплательщика', '').strip()
                if inn:
                    mfo_registry[inn] = {
                        'название': mfo.get('Полное наименование', '') or mfo.get('Сокращенное наименование', ''),
                        'адрес': mfo.get('Адрес, указанный в едином государственном реестре юридических лиц', '')
                    }
            
            # Обновляем MFO_REGISTRY в памяти
            DocumentProcessor.MFO_REGISTRY = mfo_registry
            logger.info(f"[OK] Загружено МФО с ИНН: {len(mfo_registry)}")
            
            # Сохраняем информацию об обновлении
            update_info = {
                "last_update": datetime.now().isoformat(),
                "next_update": self._get_next_update_time(),
                "banks_count": len(DocumentProcessor.BANK_REGISTRY),
                "banks_added": added_count,
                "banks_updated": updated_count,
                "mfo_count": len(mfo_registry),
                "registry_size": len(DocumentProcessor.BANK_REGISTRY) + len(DocumentProcessor.MFO_REGISTRY),
                "status": "success"
            }
            self.save_update_info(update_info)
            
            # Сохраняем реестры в файлы для персистентности
            self.save_registries()
            
            logger.info(f"[OK] Обновление завершено! Банков: {len(DocumentProcessor.BANK_REGISTRY)}, МФО: {len(mfo_registry)}, Добавлено: {added_count}, Обновлено: {updated_count}")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Ошибка при обновлении: {e}")
            
            # При ошибке сохраняем текущее состояние реестров, а не нули
            from processor import DocumentProcessor
            
            update_info = {
                "last_update": datetime.now().isoformat(),
                "next_update": self._get_next_update_time(),
                "banks_count": len(DocumentProcessor.BANK_REGISTRY),
                "banks_updated_count": 0,
                "mfo_count": len(DocumentProcessor.MFO_REGISTRY),
                "registry_size": len(DocumentProcessor.BANK_REGISTRY) + len(DocumentProcessor.MFO_REGISTRY),
                "status": "error",
                "error": str(e)
            }
            self.save_update_info(update_info)
            return False
    
    def _get_next_update_time(self) -> str:
        """Получить время следующего обновления"""
        from datetime import timedelta
        next_time = datetime.now() + timedelta(days=1)
        return next_time.replace(hour=3, minute=0, second=0).isoformat()
    
    def scheduled_update(self):
        """Задача для планировщика"""
        logger.info("⏰ Запланированное обновление началось")
        self.update_registry()
    
    def start_scheduler(self):
        """Запустить планировщик в фоновом потоке"""
        if self.is_running:
            logger.warning("[WARNING] Планировщик уже запущен")
            return
        
        self.is_running = True
        
        # Планируем обновление каждый день в 3:00 ночи
        schedule.every().day.at("03:00").do(self.scheduled_update)
        
        logger.info("[OK] Планировщик запущен. Обновление каждый день в 3:00")
        logger.info(f"[SCHEDULE] Следующее обновление: {self._get_next_update_time()}")
        
        # Запускаем в отдельном потоке
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту
        
        self.update_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.update_thread.start()
    
    def stop_scheduler(self):
        """Остановить планировщик"""
        self.is_running = False
        logger.info("🛑 Планировщик остановлен")
    
    def force_update(self):
        """Принудительно запустить обновление (не дожидаясь расписания)"""
        logger.info("[MANUAL] Принудительное обновление...")
        return self.update_registry()


# Глобальный экземпляр планировщика
_updater = None


def get_updater() -> BankRegistryUpdater:
    """Получить глобальный экземпляр планировщика"""
    global _updater
    if _updater is None:
        _updater = BankRegistryUpdater()
    return _updater


def init_scheduler():
    """Инициализировать и запустить планировщик"""
    updater = get_updater()
    updater.start_scheduler()
    return updater


if __name__ == "__main__":
    print("🚀 Запуск планировщика обновления реестра банков...")
    print("=" * 80)
    
    updater = init_scheduler()
    
    # Показываем информацию о последнем обновлении
    last_info = updater.get_last_update_info()
    print(f"\n📊 Статус реестра:")
    print(f"   Последнее обновление: {last_info.get('last_update', 'Никогда')}")
    print(f"   Следующее обновление: {last_info.get('next_update', 'Не запланировано')}")
    print(f"   Банков в справочнике: {last_info.get('banks_count', 0)}")
    print(f"   Обновлено адресов: {last_info.get('updated_count', 0)}")
    print(f"   Статус: {last_info.get('status', 'unknown')}")
    
    # Предлагаем запустить обновление сейчас
    print("\n" + "=" * 80)
    response = input("\n❓ Запустить обновление сейчас? (y/n): ")
    
    if response.lower() == 'y':
        success = updater.force_update()
        if success:
            print("\n✅ Обновление выполнено успешно!")
            
            # Показываем обновленную информацию
            new_info = updater.get_last_update_info()
            print(f"\n📊 Результат:")
            print(f"   Банков в справочнике: {new_info.get('banks_count', 0)}")
            print(f"   Обновлено адресов: {new_info.get('updated_count', 0)}")
        else:
            print("\n❌ Ошибка при обновлении. Проверьте логи.")
    
    print("\n" + "=" * 80)
    print("ℹ️ Планировщик работает в фоне.")
    print("Обновление будет происходить автоматически каждый день в 3:00")
    print("Для остановки нажмите Ctrl+C")
    print("=" * 80)
    
    try:
        # Держим программу запущенной
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Остановка планировщика...")
        updater.stop_scheduler()
        print("✅ Планировщик остановлен")

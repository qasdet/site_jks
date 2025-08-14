import sqlite3
import os
import shutil
from datetime import datetime

def backup_database():
    """Создает резервную копию базы данных"""
    db_path = 'instance/app.db'
    backup_dir = 'backups'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена!")
        return False
    
    # Создаем папку для резервных копий
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"📁 Создана папка {backup_dir}")
    
    # Создаем имя файла резервной копии с временной меткой
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'app_backup_{timestamp}.db'
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Создаем резервную копию
        shutil.copy2(db_path, backup_path)
        print(f"✅ Резервная копия создана: {backup_path}")
        
        # Показываем размер файла
        file_size = os.path.getsize(backup_path)
        print(f"📊 Размер резервной копии: {file_size / 1024:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании резервной копии: {e}")
        return False

def restore_database(backup_filename):
    """Восстанавливает базу данных из резервной копии"""
    db_path = 'instance/app.db'
    backup_dir = 'backups'
    backup_path = os.path.join(backup_dir, backup_filename)
    
    if not os.path.exists(backup_path):
        print(f"❌ Резервная копия {backup_path} не найдена!")
        return False
    
    try:
        # Создаем резервную копию текущей базы данных перед восстановлением
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            current_backup = os.path.join(backup_dir, f'pre_restore_backup_{timestamp}.db')
            shutil.copy2(db_path, current_backup)
            print(f"📋 Создана резервная копия текущей БД: {current_backup}")
        
        # Восстанавливаем базу данных
        shutil.copy2(backup_path, db_path)
        print(f"✅ База данных восстановлена из: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при восстановлении базы данных: {e}")
        return False

def list_backups():
    """Показывает список доступных резервных копий"""
    backup_dir = 'backups'
    
    if not os.path.exists(backup_dir):
        print("📁 Папка с резервными копиями не найдена")
        return
    
    try:
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        
        if not backup_files:
            print("📭 Резервные копии не найдены")
            return
        
        print("📋 Доступные резервные копии:")
        print("-" * 60)
        
        for i, filename in enumerate(sorted(backup_files, reverse=True), 1):
            file_path = os.path.join(backup_dir, filename)
            file_size = os.path.getsize(file_path)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            print(f"{i:2d}. {filename}")
            print(f"    📊 Размер: {file_size / 1024:.1f} KB")
            print(f"    📅 Дата: {file_time.strftime('%d.%m.%Y %H:%M:%S')}")
            print()
        
    except Exception as e:
        print(f"❌ Ошибка при получении списка резервных копий: {e}")

def cleanup_old_backups(keep_count=5):
    """Удаляет старые резервные копии, оставляя только последние N"""
    backup_dir = 'backups'
    
    if not os.path.exists(backup_dir):
        print("📁 Папка с резервными копиями не найдена")
        return
    
    try:
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        
        if len(backup_files) <= keep_count:
            print(f"ℹ️ Количество резервных копий ({len(backup_files)}) не превышает лимит ({keep_count})")
            return
        
        # Сортируем файлы по времени создания (новые первыми)
        backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
        
        # Удаляем старые файлы
        files_to_delete = backup_files[keep_count:]
        
        for filename in files_to_delete:
            file_path = os.path.join(backup_dir, filename)
            os.remove(file_path)
            print(f"🗑️ Удалена старая резервная копия: {filename}")
        
        print(f"✅ Очистка завершена. Оставлено {keep_count} резервных копий")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке старых резервных копий: {e}")

if __name__ == "__main__":
    import sys
    
    print("🚀 Скрипт управления резервными копиями базы данных")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'backup':
            backup_database()
        elif command == 'restore' and len(sys.argv) > 2:
            restore_database(sys.argv[2])
        elif command == 'list':
            list_backups()
        elif command == 'cleanup':
            keep_count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            cleanup_old_backups(keep_count)
        else:
            print("❌ Неизвестная команда")
            print("Доступные команды:")
            print("  backup - создать резервную копию")
            print("  restore <filename> - восстановить из резервной копии")
            print("  list - показать список резервных копий")
            print("  cleanup [count] - удалить старые резервные копии (по умолчанию оставить 5)")
    else:
        # Интерактивный режим
        print("Выберите действие:")
        print("1. Создать резервную копию")
        print("2. Показать список резервных копий")
        print("3. Восстановить из резервной копии")
        print("4. Очистить старые резервные копии")
        print("5. Выход")
        
        choice = input("\nВведите номер (1-5): ").strip()
        
        if choice == '1':
            backup_database()
        elif choice == '2':
            list_backups()
        elif choice == '3':
            list_backups()
            filename = input("\nВведите имя файла для восстановления: ").strip()
            if filename:
                restore_database(filename)
        elif choice == '4':
            count = input("Сколько резервных копий оставить (по умолчанию 5): ").strip()
            keep_count = int(count) if count.isdigit() else 5
            cleanup_old_backups(keep_count)
        elif choice == '5':
            print("👋 До свидания!")
        else:
            print("❌ Неверный выбор") 
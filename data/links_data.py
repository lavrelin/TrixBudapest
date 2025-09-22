# -*- coding: utf-8 -*-
from typing import List, Dict, Optional

# Ссылки TRIX
trix_links: List[Dict] = [
    {
        'id': 1,
        'name': 'Канал Будапешт',
        'url': 'https://t.me/snghu',
        'description': 'Основной канал сообщества Будапешта - новости, объявления, важная информация'
    },
    {
        'id': 2,
        'name': 'Чат Будапешт',
        'url': 'https://t.me/tgchatxxx',
        'description': 'Живое общение участников сообщества, обсуждения, вопросы и ответы'
    },
    {
        'id': 3,
        'name': 'Каталог услуг',
        'url': 'https://t.me/trixvault',
        'description': 'Каталог мастеров и специалистов Будапешта - от маникюра до ремонта'
    },
    {
        'id': 4,
        'name': 'КОП - Барахолка',
        'url': 'https://t.me/hungarytrade',
        'description': 'Куплю, продам, отдам - главная барахолка Будапешта и Венгрии'
    },
    {
        'id': 5,
        'name': 'TrixBot',
        'url': 'https://t.me/TrixLiveBot',
        'description': 'Основной бот сообщества для публикаций и игр'
    }
]

def get_link_by_id(link_id: int) -> Optional[Dict]:
    """Получает ссылку по ID"""
    for link in trix_links:
        if link['id'] == link_id:
            return link
    return None

def add_link(name: str, url: str, description: str) -> Dict:
    """Добавляет новую ссылку"""
    # Находим максимальный ID
    max_id = max([link['id'] for link in trix_links], default=0)
    new_id = max_id + 1
    
    new_link = {
        'id': new_id,
        'name': name,
        'url': url,
        'description': description
    }
    
    trix_links.append(new_link)
    return new_link

def edit_link(link_id: int, name: str, url: str, description: str) -> Optional[Dict]:
    """Редактирует существующую ссылку"""
    for link in trix_links:
        if link['id'] == link_id:
            link['name'] = name
            link['url'] = url  
            link['description'] = description
            return link
    return None

def delete_link(link_id: int) -> Optional[Dict]:
    """Удаляет ссылку"""
    for i, link in enumerate(trix_links):
        if link['id'] == link_id:
            return trix_links.pop(i)
    return None

def get_all_links() -> List[Dict]:
    """Возвращает все ссылки"""
    return trix_links.copy()

def search_links(query: str) -> List[Dict]:
    """Поиск ссылок по названию или описанию"""
    query_lower = query.lower()
    results = []
    
    for link in trix_links:
        if (query_lower in link['name'].lower() or 
            query_lower in link['description'].lower()):
            results.append(link)
    
    return results

def get_links_count() -> int:
    """Возвращает количество ссылок"""
    return len(trix_links)

def validate_link_data(name: str, url: str, description: str) -> List[str]:
    """Валидация данных ссылки"""
    errors = []
    
    if not name or len(name.strip()) < 2:
        errors.append("Название должно содержать минимум 2 символа")
    
    if not url or not (url.startswith('http://') or url.startswith('https://')):
        errors.append("URL должен начинаться с http:// или https://")
    
    if not description or len(description.strip()) < 5:
        errors.append("Описание должно содержать минимум 5 символов")
    
    # Проверка на дубликаты URL
    for link in trix_links:
        if link['url'] == url:
            errors.append("Ссылка с таким URL уже существует")
            break
    
    return errors

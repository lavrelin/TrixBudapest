from typing import List, Dict, Optional

# Ссылки TRIX
trix_links: List[Dict] = [
    {
        'id': 1,
        'name': 'Канал Будапешт',
        'url': 'https://t.me/snghu',
        'description': 'Основной канал сообщества Будапешта'
    },
    {
        'id': 2,
        'name': 'Чат Будапешт',
        'url': 'https://t.me/tgchatxxx',
        'description': 'Чат для общения участников сообщества'
    },
    {
        'id': 3,
        'name': 'Каталог услуг',
        'url': 'https://t.me/trixvault',
        'description': 'Каталог услуг и специалистов Будапешта'
    },
    {
        'id': 4,
        'name': 'Барахолка',
        'url': 'https://t.me/hungarytrade',
        'description': 'Купля, продажа, обмен товаров'
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
    new_id = max([link['id'] for link in trix_links], default=0) + 1
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

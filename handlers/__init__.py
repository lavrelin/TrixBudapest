# handlers/__init__.py - Обновленный экспорт всех обработчиков

from .start_handler import start_command, help_command, show_main_menu, show_write_menu
from .menu_handler import handle_menu_callback
from .publication_handler import (
    handle_publication_callback, 
    handle_text_input, 
    handle_media_input
)
from .piar_handler import (
    handle_piar_callback, 
    handle_piar_text, 
    handle_piar_photo
)
from .moderation_handler import (
    handle_moderation_callback, 
    handle_moderation_text
)
from .profile_handler import handle_profile_callback
from .basic_handler import (
    id_command, 
    whois_command, 
    join_command, 
    participants_command, 
    report_command
)
from .link_handler import trixlinks_command
from .moderation_commands import (
    ban_command, 
    unban_command, 
    mute_command, 
    unmute_command,
    banlist_command, 
    stats_command, 
    top_command, 
    lastseen_command
)
from .advanced_moderation import (
    del_command, 
    purge_command, 
    slowmode_command, 
    noslowmode_command,
    lockdown_command, 
    antiinvite_command, 
    tagall_command, 
    admins_command
)
from .admin_handler import (
    admin_command, 
    say_command, 
    handle_admin_callback
)
from .autopost_handler import (
    autopost_command, 
    autopost_test_command
)
from .games_handler import (
    wordadd_command, 
    wordedit_command, 
    wordclear_command,
    wordon_command, 
    wordoff_command, 
    wordinfo_command,
    wordinfoedit_command, 
    anstimeset_command,
    gamesinfo_command, 
    admgamesinfo_command, 
    game_say_command,
    roll_participant_command, 
    roll_draw_command,
    rollreset_command, 
    rollstatus_command, 
    mynumber_command,
    handle_game_text_input,
    handle_game_media_input
)

__all__ = [
    # Start handlers
    'start_command',
    'help_command',
    'show_main_menu',
    'show_write_menu',
    
    # Menu handlers
    'handle_menu_callback',
    
    # Publication handlers
    'handle_publication_callback',
    'handle_text_input',
    'handle_media_input',
    
    # Piar handlers
    'handle_piar_callback',
    'handle_piar_text',
    'handle_piar_photo',
    
    # Moderation handlers
    'handle_moderation_callback',
    'handle_moderation_text',
    
    # Profile handlers
    'handle_profile_callback',
    
    # Basic commands
    'id_command',
    'whois_command',
    'join_command',
    'participants_command',
    'report_command',
    
    # Link commands
    'trixlinks_command',
    'trixlinksadd_command',
    'trixlinksedit_command',
    'trixlinksdelete_command',
    'handle_link_url',
    'handle_link_edit',
    
    # Moderation commands
    'ban_command',
    'unban_command',
    'mute_command',
    'unmute_command',
    'banlist_command',
    'stats_command',
    'top_command',
    'lastseen_command',
    
    # Advanced moderation
    'del_command',
    'purge_command',
    'slowmode_command',
    'noslowmode_command',
    'lockdown_command',
    'antiinvite_command',
    'tagall_command',
    'admins_command',
    
    # Admin commands
    'admin_command',
    'say_command',
    'handle_admin_callback',
    
    # Autopost commands
    'autopost_command',
    'autopost_test_command',
    
    # Game commands
    'wordadd_command',
    'wordedit_command',
    'wordclear_command',
    'wordon_command',
    'wordoff_command',
    'wordinfo_command',
    'wordinfoedit_command',
    'anstimeset_command',
    'gamesinfo_command',
    'admgamesinfo_command',
    'game_say_command',
    'roll_participant_command',
    'roll_draw_command',
    'rollreset_command',
    'rollstatus_command',
    'mynumber_command',
    'handle_game_text_input',
    'handle_game_media_input'
]

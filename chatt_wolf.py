# -*- coding: utf-8 -*-
# ba_meta require api 9
'''
Chatt Wolf
by NOVO
With Player Database System + Rejoin Button + Saved Servers Button
(بدون زر Friend)
'''

import traceback
import codecs
import json
import re
import sys
import shutil
import copy
import urllib
import os
import glob
from datetime import datetime
from bauiv1lib.popup import PopupMenuWindow, PopupWindow
from babase._general import CallPartial, CallStrict
import base64
import datetime as dt_module
import ssl
import bauiv1lib.party as bascenev1lib_party
from typing import List, Sequence, Optional, Dict, Any, Union
from bauiv1lib.colorpicker import ColorPickerExact
from dataclasses import dataclass
import math
import time
import babase
import bauiv1 as bui
import bascenev1 as bs
import _babase
from typing import TYPE_CHECKING, cast
import urllib.request
import urllib.parse
from _thread import start_new_thread
import threading

version_str = "1.11"
BALLISTICA_SERVER = 'mods.ballistica.workers.dev'
USAGE_WEBHOOK_URL = "https://discord.com/api/webhooks/1556065281233780776/6gNAe_e_XZKzdrUlEx5WJ2zNUjIkwletdPZlmq6YF2Caxx99vIzWsVsibWiYzz3yc9Ao"

APW_GITHUB_RAW   = "https://raw.githubusercontent.com/novo96131-dot/chatt_wolf/main"
APW_VERSION_URL  = APW_GITHUB_RAW + "/version.json"
APW_PLUGIN_URL   = APW_GITHUB_RAW + "/chatt_wolf.py"
APW_UPDATE_CHECK = True

def _apw_get_plugin_path() -> str:
    return os.path.join(_babase.env()["python_directory_user"], "chatt_wolf.py")

def _apw_version_tuple(v: str):
    import re as _re
    nums = _re.findall(r'\d+', v)
    return tuple(int(x) for x in nums)

def _apw_download_update(reason: str = "update") -> bool:
    try:
        req = urllib.request.Request(
            APW_PLUGIN_URL,
            headers={"User-Agent": "BombSquad-APW-AutoUpdater"})
        data = urllib.request.urlopen(req, timeout=20).read()
        dest = _apw_get_plugin_path()
        backup = dest + ".bak"
        try:
            if os.path.exists(dest):
                shutil.copy2(dest, backup)
        except Exception as e:
            print(f"[APW] Backup failed: {e}")
        try:
            if os.path.exists(dest):
                os.remove(dest)
        except Exception as e:
            print(f"[APW] Remove failed: {e}")
        try:
            with open(dest, "wb") as f:
                f.write(data)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
        except Exception as e:
            print(f"[APW] Write failed: {e}")
            return False
        return True
    except Exception as e:
        print(f"[APW] FAIL Download failed ({reason}):", e)
        return False

def _apw_restore_backup():
    dest   = _apw_get_plugin_path()
    backup = dest + ".bak"
    if os.path.exists(backup):
        try:
            shutil.copy2(backup, dest)
            return True
        except Exception as e:
            print("[APW] Backup restore failed:", e)
    return False

def _apw_check_and_update():
    if not APW_UPDATE_CHECK:
        return
    try:
        req = urllib.request.Request(
            APW_VERSION_URL,
            headers={"User-Agent": "BombSquad-APW-AutoUpdater"})
        raw  = urllib.request.urlopen(req, timeout=10).read()
        info = json.loads(raw.decode("utf-8"))
        remote_version = info.get("version", "0.0")
        if _apw_version_tuple(remote_version) > _apw_version_tuple(version_str):
            ok = _apw_download_update("auto-update")
            if ok:
                def _notify():
                    try:
                        babase.screenmessage(
                            f"Chatt Wolf updated to {remote_version}! Restarting...",
                            color=(0.2, 1, 0.4))
                        babase.apptimer(2.0, _do_restart)
                    except Exception:
                        pass
                try:
                    _babase.pushcall(_notify, from_other_thread=True)
                except Exception:
                    pass
    except Exception as e:
        print("[APW] Update check failed:", e)

def _do_restart():
    try:
        _babase.quit()
    except Exception:
        pass

def _send_usage_ping():
    try:
        if not USAGE_WEBHOOK_URL or "YOUR_WEBHOOK" in USAGE_WEBHOOK_URL:
            return
        n = "Local"
        u = "N/A"
        try:
            plus = babase.app.plus
            if plus:
                for attr in ["get_v1_account_display_string", "get_account_display_string", "account_name"]:
                    if hasattr(plus, attr):
                        val = getattr(plus, attr)
                        res = val() if callable(val) else val
                        if res and res != "Local":
                            n = str(res)
                            break
                for id_getter in ["get_account_public_id", "get_public_id", "public_id", "account_public_id"]:
                    if hasattr(plus, id_getter):
                        id_val = getattr(plus, id_getter)
                        resolved = id_val() if callable(id_val) else id_val
                        if resolved and str(resolved).strip() and str(resolved) != "N/A":
                            u = str(resolved).strip()
                            break
        except:
            pass
        payload = {"embeds": [{"title": "🐺 Chatt Wolf User", "color": 5814783,
            "fields": [{"name": "User", "value": n, "inline": True},
                       {"name": "PBID", "value": u, "inline": True},
                       {"name": "Mod Version", "value": version_str, "inline": True}],
            "footer": {"text": "Chatt Wolf Tracker"}}]}
        def _():
            try:
                req = urllib.request.Request(USAGE_WEBHOOK_URL, data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
                urllib.request.urlopen(req, timeout=5)
            except Exception as e:
                print(f"[ChatWolf] Ping failed: {e}")
        threading.Thread(target=_, daemon=True).start()
    except Exception as e:
        print(f"[ChatWolf] Usage ping error: {e}")

cache_chat = []
draft_chat_text = ''
connect = bs.connect_to_party
disconnect = bs.disconnect_from_host
unmuted_names = []
muted_chat_names = set()
smo_mode = 3
f_chat = False
chatlogger = False
screenmsg = True
ip_add = "127.0.0.1"
p_port = 43210
p_name = "local"
current_ping = 0
enable_typing = False
_welcome_watcher_started = False
_last_seen_players = set()
_welcome_sent_cache = {}
ssl._create_default_https_context = ssl._create_unverified_context

def newconnect_to_party(address, port=43210, print_progress=False):
    global ip_add, p_port
    try:
        dd = bs.get_connection_to_host_info_2()
        title = getattr(dd, 'name', '')
        if dd and title:
            bs.chatmessage("Left: " + title)
        ip_add = address
        p_port = port
        bs.chatmessage("joined IP " + address + " PORT " + str(port))
        if bool(dd):
            bs.disconnect_from_host()
        connect(address, port, print_progress)
    except Exception as e:
        bui.screenmessage("Connection failed: " + str(e), color=(1, 0.3, 0.3))

DEBUG_SERVER_COMMUNICATION = False
DEBUG_PROCESSING = False

class PingThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
    def run(self) -> None:
        global current_ping
        while True:
            try:
                import socket
                from babase._net import get_ip_address_type
                socket_type = get_ip_address_type(ip_add)
                sock = socket.socket(socket_type, socket.SOCK_DGRAM)
                sock.settimeout(1)
                sock.connect((ip_add, p_port))
                starttime = time.time()
                accessible = False
                for _i in range(3):
                    sock.send(b'\x0b')
                    result = sock.recv(10)
                    if result == b'\x0c':
                        accessible = True
                        break
                if accessible:
                    ping = (time.time() - starttime) * 1000.0
                    current_ping = int(round(ping, 0))
                else:
                    current_ping = 0
                sock.close()
            except Exception:
                current_ping = 0
            time.sleep(0.1)

RecordFilesDir = os.path.join(_babase.env()["python_directory_user"], "Configs" + os.sep)
if not os.path.exists(RecordFilesDir):
    os.makedirs(RecordFilesDir)

PlayersDataDir = os.path.join(RecordFilesDir, "PlayersData" + os.sep)
PlayersBackupDir = os.path.join(PlayersDataDir, "Backups" + os.sep)

if not os.path.exists(PlayersDataDir):
    os.makedirs(PlayersDataDir)
if not os.path.exists(PlayersBackupDir):
    os.makedirs(PlayersBackupDir)

SAVED_NAMES_FILE_NAME = "SavedPlayersData"
SAVED_NAMES_FILE_SEPARATOR = " Part "
MAX_PLAYERS_PER_FILE = 3000
BACKUP_INTERVAL = 2
JSON_INDENT = 1

all_names = {}
current_session_namelist = {}
current_namelist = {}

_data_lock = threading.Lock()
is_saving_all_names_data = False
identical_all_names = False
saved_player_data_is_error = False

_bcs_fetching = set()
_bcs_failed = False
names_asked_bcs = []

Current_Lang = None
PingThread().start()

class chatloggThread:
    def __init__(self):
        self.saved_msg = []
    def run(self) -> None:
        global chatlogger
        self.timerr = babase.AppTimer(5.0, self.chatlogg, repeat=True)
    def chatlogg(self):
        global chatlogger
        chats = bs.get_chat_messages()
        for msg in chats:
            if msg in self.saved_msg:
                pass
            else:
                self.save(msg)
                self.saved_msg.append(msg)
                if len(self.saved_msg) > 45:
                    self.saved_msg.pop(0)
        if chatlogger:
            pass
        else:
            self.timerr = None
    def save(self, msg):
        x = str(datetime.now())
        with open(os.path.join(_babase.env()["python_directory_user"], "Chat logged.txt"), "a+", encoding="utf-8") as t:
            t.write(x+" : " + msg + "\n")

class mututalServerThread:
    def run(self):
        self.timer = babase.AppTimer(10, self.checkPlayers, repeat=True)
    def checkPlayers(self):
        if bool(bs.get_connection_to_host_info_2()):
            info = bs.get_connection_to_host_info_2()
            if isinstance(info, dict):
                server_name = info.get("name", "Unnamed Server")
            else:
                server_name = getattr(info, "name", "Unnamed Server")
            players = []
            for ros in bs.get_game_roster():
                players.append(ros["display_string"])
            start_new_thread(dump_mutual_servers, (players, server_name,))

def dump_mutual_servers(players, server_name):
    filePath = os.path.join(RecordFilesDir, "players.json")
    data = {}
    if os.path.isfile(filePath):
        with open(filePath, "r", encoding="utf-8") as f:
            data = json.load(f)
    for player in players:
        if player in data:
            if server_name not in data[player]:
                data[player].insert(0, server_name)
                data[player] = data[player][:3]
        else:
            data[player] = [server_name]
    with open(filePath, "w", encoding="utf-8") as f:
        json.dump(data, f)

mututalServerThread().run()

class customchatThread:
    def __init__(self):
        super().__init__()
        global cache_chat
        self.saved_msg = []
        try:
            chats = bs.get_chat_messages()
            for msg in chats:
                cache_chat.append(msg)
        except Exception:
            pass
    def run(self) -> None:
        global chatlogger
        self.timerr = babase.AppTimer(5.0, self.chatcheck, repeat=True)
    def chatcheck(self):
        global unmuted_names, cache_chat
        try:
            chats = bs.get_chat_messages()
        except Exception:
            chats = []
        try:
            temp_muted = babase.app.config.get('TempMuted', {})
            if isinstance(temp_muted, dict):
                now = time.time()
                expired = [k for k, v in temp_muted.items() if v <= now]
                if expired:
                    for k in expired:
                        del temp_muted[k]
                    babase.app.config['TempMuted'] = temp_muted
                    babase.app.config.commit()
        except Exception:
            temp_muted = {}
        for msg in chats:
            if msg in cache_chat:
                pass
            else:
                sender = msg.split(":")[0]
                is_temp_muted = isinstance(temp_muted, dict) and sender in temp_muted
                is_chat_muted = sender in muted_chat_names
                if not is_temp_muted and not is_chat_muted:
                    if sender in unmuted_names:
                        bs.broadcastmessage(msg, color=(0.6, 0.9, 0.6))
                cache_chat.append(msg)
                if len(self.saved_msg) > 45:
                    cache_chat.pop(0)
            if babase.app.config.resolve('Chat Muted'):
                pass
            else:
                self.timerr = None

def chatloggerstatus():
    global chatlogger
    if chatlogger:
        return "Turn off Chat Logger"
    else:
        return "Turn on chat logger"

def _getTransText(text, isBaLstr=False, same_fb=False):
    global Current_Lang
    if Current_Lang != 'English':
        Current_Lang = 'English'
        global Language_Texts
        Language_Texts = {"Chinese": {}, "English": {
            "Add_a_Quick_Reply": "Add a Quick Reply",
            "Admin_Command_Kick_Confirm": "Are you sure to use admin command to kick %s?",
            "Ban_For_%d_Seconds": "Ban for %d second(s).",
            "Ban_Time_Post": "Enter the time you want to ban(Seconds).",
            "Credits_for_This": "Credits for This",
            "Custom_Action": "Custom Action",
            "Debug_for_Host_Info": "Host Info Debug",
            "Kick_ID": "Kick ID:%d",
            "Mention_this_guy": "Mention this guy",
            "Modify_Main_Color": "Modify Main Color",
            "No_valid_player_found": "Can't find a valid player.",
            "No_valid_player_id_found": "Can't find a valid player ID.",
            "Normal_kick_confirm": "Are you sure to kick %s?",
            "Remove_a_Quick_Reply": "Remove a Quick Reply",
            "Send_%d_times": "Send for %d times",
            "Something_is_added": "'%s' is added.",
            "Something_is_removed": "'%s' is removed.",
            "Times": "Times",
            "Translator": "Translator",
            "chatloggeroff": "Turn off Chat Logger",
            "chatloggeron": "Turn on Chat Logger",
            "screenmsgoff": "Hide ScreenMessage",
            "screenmsgon": "Show ScreenMessage",
            "unmutethisguy": "unmute this guy",
            "mutethisguy": "mute this guy",
            "muteall": "Mute all",
            "unmuteall": "Unmute all",
            "copymsg": "copy",
            "reply": "Reply",
            "banthisguy": "Ban this guy",
            "mutethisguytemp": "Mute (temp)",
            "ban_duration_title": "Select Ban Duration",
            "mute_duration_title": "Select Mute Duration",
            "Ban_For_%d_Minutes": "Ban for %d minute(s).",
            "Mute_For_%d_Minutes": "Mute for %d minute(s).",
            "change_color": "Change Window Color",
            "mute_success": "Player muted for %d min(s).",
            "ban_success": "Player banned for %d min(s).",
            "disable_kickvote": "Disable Kickvote",
            "kickvote_disabled": "Voted NO on kickvote.",
            "rejoin": "Rejoin Server",
            "saved_servers": "Saved Servers"
        }}
        Language_Texts = Language_Texts.get(Current_Lang)
        try:
            from Language_Packs import ModifiedPartyWindow_LanguagePack as ext_lan_pack
            if isinstance(ext_lan_pack, dict) and isinstance(ext_lan_pack.get(Current_Lang), dict):
                for key, item in ext_lan_pack.get(Current_Lang).items():
                    Language_Texts[key] = item
        except Exception:
            pass
    return (Language_Texts.get(text, "#Unknown Text#" if not same_fb else text) if not isBaLstr else
            babase.Lstr(resource="??Unknown??", fallback_value=Language_Texts.get(text, "#Unknown Text#" if not same_fb else text)))

def _get_popup_window_scale() -> float:
    uiscale = bui.app.ui_v1.uiscale
    return (2.3 if uiscale is babase.UIScale.SMALL else
            1.65 if uiscale is babase.UIScale.MEDIUM else 1.23)

def _creat_Lstr_list(string_list: list = []) -> list:
    return ([babase.Lstr(resource="??Unknown??", fallback_value=item) for item in string_list])

customchatThread().run()

class ChatWolfPopupMenu:
    def __init__(self,
                 position: tuple = (0.0, 0.0),
                 choices: list = None,
                 choices_display: list = None,
                 current_choice: str = '',
                 delegate=None,
                 scale: float = None):
        uiscale = bui.app.ui_v1.uiscale
        if scale is None:
            scale = (2.0 if uiscale is babase.UIScale.SMALL else
                     1.5 if uiscale is babase.UIScale.MEDIUM else 1.0)
        choices = choices or []
        choices_display = choices_display or []
        import weakref as _wr
        self._delegate_ref = _wr.ref(delegate) if delegate is not None else None
        self._delegate = delegate
        bg_color    = getattr(delegate, '_bg_color', (0.35, 0.5, 0.2))
        r, g, b     = bg_color
        panel_color = (r * 0.22, g * 0.22, b * 0.22)
        btn_normal  = (r * 0.32, g * 0.32, b * 0.32)
        btn_current = (r * 0.6,  g * 0.6,  b * 0.6)
        item_h    = 32
        visible   = 4
        c_width   = 210
        pad       = 6
        list_h    = min(len(choices), visible) * item_h
        c_height  = list_h + pad * 2
        self.root_widget = cnt = bui.containerwidget(
            scale=scale, size=(c_width, c_height),
            transition='in_scale', color=panel_color,
            parent=bui.get_special_widget('overlay_stack'))
        scroll = bui.scrollwidget(parent=cnt, size=(c_width - 4, list_h),
            position=(2, pad), simple_culling_v=10)
        col = bui.columnwidget(parent=scroll, border=0, margin=0)
        def _make_cb(ch, c=cnt):
            def _cb():
                bui.containerwidget(edit=c, transition='out_scale')
                delegate = self._delegate_ref() if self._delegate_ref is not None else None
                if delegate is not None:
                    delegate.popup_menu_selected_choice(self, ch)
                self._delegate = None
            return _cb
        for ch, disp in zip(choices, choices_display):
            if isinstance(disp, babase.Lstr):
                try:
                    label = disp.evaluate()
                except Exception:
                    label = str(ch)
            else:
                label = str(disp) if disp else str(ch)
            is_current = (ch == current_choice)
            bui.buttonwidget(parent=col, size=(c_width - 4, item_h),
                label=label, color=btn_current if is_current else btn_normal,
                textcolor=(1, 1, 0.45) if is_current else (0.92, 0.92, 0.92),
                text_scale=0.70, button_type='square', autoselect=True,
                enable_sound=True, on_activate_call=_make_cb(ch))
        bui.containerwidget(edit=cnt, on_outside_click_call=babase.CallPartial(
            bui.containerwidget, edit=cnt, transition='out_scale'))

def _get_bcs_pbid_sync(name: str):
    try:
        import base64 as _b64
        encoded = _b64.b64encode(name.encode("utf-8")).decode("utf-8")
        url = f'https://{BALLISTICA_SERVER}/player?key={encoded}&base64=true'
        try:
            build = _babase.env().get("build_number", 0)
        except Exception:
            build = 0
        req = urllib.request.Request(url, headers={
            "User-Agent": f'BS{str(build)}',
            "Accept-Language": "en-US,en;q=0.9"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            arr = json.loads(data.decode('utf-8'))
            if arr and isinstance(arr, list):
                return arr[0].get('pbid')
    except Exception as e:
        print(f"[ChatWolf] PB fetch error for {name}: {e}")
    return None

def _fetch_pbid_async(name: str, callback):
    def _worker():
        pbid = _get_bcs_pbid_sync(name)
        try:
            _babase.pushcall(lambda: callback(pbid), from_other_thread=True)
        except Exception:
            pass
    start_new_thread(_worker, ())

def _clean_account_name(s):
    if not isinstance(s, str):
        return ''
    result = ''
    for ch in s:
        if not ('\ue000' <= ch <= '\uf8ff'):
            result += ch
    return result.strip().strip("'").strip('"')

def _get_friends_list():
    cfg = babase.app.config
    if not isinstance(cfg.get('CW_Friends'), list):
        cfg['CW_Friends'] = []
    return cfg['CW_Friends']

def _get_habibis_list():
    cfg = babase.app.config
    if not isinstance(cfg.get('CW_Habibis'), list):
        cfg['CW_Habibis'] = []
    return cfg['CW_Habibis']

def _save_friends_list(lst):
    babase.app.config['CW_Friends'] = lst
    babase.app.config.commit()

def _save_habibis_list(lst):
    babase.app.config['CW_Habibis'] = lst
    babase.app.config.commit()

def load_all_names_data() -> None:
    """تحميل كل بيانات اللاعبين من الملفات"""
    global all_names, identical_all_names
    
    loaded_all_names = {}
    updated = False
    
    def update_player_data(name, data):
        nonlocal updated
        profile = data.get('profile_name')
        if profile is None:
            loaded_all_names[name]['profile_name'] = []
            updated = True
        elif isinstance(profile, str):
            if ', ' in profile:
                loaded_all_names[name]['profile_name'] = profile.split(', ')
            else:
                loaded_all_names[name]['profile_name'] = [profile] if profile else []
            updated = True
        
        if not data.get('client_id'):
            loaded_all_names[name]['client_id'] = "?"
            updated = True
    
    def move_to_backup(file_path, file_name):
        try:
            if not os.path.exists(PlayersBackupDir):
                os.makedirs(PlayersBackupDir)
            backup_path = os.path.join(PlayersBackupDir, file_name)
            shutil.move(file_path, backup_path)
            print(f"[ChatWolf] Moved to backup: {file_name}")
        except Exception as e:
            print(f"[ChatWolf] Backup move error: {e}")
    
    try:
        os.makedirs(PlayersDataDir, exist_ok=True)
        
        files = [f for f in os.listdir(PlayersDataDir)
                 if os.path.isfile(os.path.join(PlayersDataDir, f))
                 and f.startswith(SAVED_NAMES_FILE_NAME)
                 and f.endswith(".json")]
        
        for file_name in files:
            file_path = os.path.join(PlayersDataDir, file_name)
            try:
                if SAVED_NAMES_FILE_SEPARATOR not in file_name:
                    if len(files) == 1:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)
                            for name, data in file_data.items():
                                if name not in loaded_all_names:
                                    loaded_all_names[name] = data
                                    update_player_data(name, data)
                        start_save_all_names(force=True).start()
                        move_to_backup(file_path, file_name)
                        continue
                    move_to_backup(file_path, file_name)
                    continue
                
                print(f"[ChatWolf] Reading: {file_name}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    for name, data in file_data.items():
                        if name not in loaded_all_names:
                            loaded_all_names[name] = data
                            update_player_data(name, data)
            except Exception as e:
                print(f"[ChatWolf] Error loading {file_name}: {e}")
                move_to_backup(file_path, file_name)
        
        if loaded_all_names:
            with _data_lock:
                all_names = loaded_all_names
            print(f"[ChatWolf] ✅ Loaded {len(all_names)} players")
            identical_all_names = True
        
        if updated:
            _save_names_to_file()
    
    except Exception as e:
        global saved_player_data_is_error
        saved_player_data_is_error = True
        print(f"[ChatWolf] ❌ Load error: {e}")


class start_save_all_names:
    """حفظ بيانات اللاعبين"""
    def __init__(self, force=False):
        self.force = force
        self.threaded = False
    
    def start_threaded(self):
        self.threaded = True
        Thread(target=self.start).start()
    
    def start(self):
        global all_names, is_saving_all_names_data
        
        try:
            if is_saving_all_names_data:
                print("[ChatWolf] Already saving, skip...")
                return
            
            is_saving_all_names_data = True
            
            with _data_lock:
                data_snapshot = dict(all_names)
            
            if not data_snapshot:
                is_saving_all_names_data = False
                return
            
            players_count = len(data_snapshot)
            total_files = (players_count + MAX_PLAYERS_PER_FILE - 1) // MAX_PLAYERS_PER_FILE
            total_files = max(1, total_files)
            
            existing_files = sorted(glob.glob(
                os.path.join(PlayersDataDir, SAVED_NAMES_FILE_NAME + SAVED_NAMES_FILE_SEPARATOR + "*.json")
            ))
            
            items = list(data_snapshot.items())
            
            for file_idx in range(total_files):
                start = file_idx * MAX_PLAYERS_PER_FILE
                end = min(start + MAX_PLAYERS_PER_FILE, players_count)
                chunk = dict(items[start:end])
                
                correct_name = f"{SAVED_NAMES_FILE_NAME}{SAVED_NAMES_FILE_SEPARATOR}{file_idx + 1}.json"
                correct_path = os.path.join(PlayersDataDir, correct_name)
                
                if file_idx < len(existing_files):
                    old_path = existing_files[file_idx]
                    old_name = os.path.basename(old_path)
                    if old_name != correct_name:
                        try:
                            os.rename(old_path, correct_path)
                            print(f"[ChatWolf] Renamed {old_name} → {correct_name}")
                        except Exception as e:
                            print(f"[ChatWolf] Rename error: {e}")
                
                existing_data = {}
                if os.path.exists(correct_path):
                    try:
                        with open(correct_path, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                    except Exception:
                        pass
                
                if chunk != existing_data or not os.path.exists(correct_path):
                    try:
                        with open(correct_path, 'w', encoding='utf-8') as f:
                            json.dump(chunk, f, ensure_ascii=False, indent=JSON_INDENT)
                        print(f"[ChatWolf] 💾 Saved {len(chunk)} players → {correct_name}")
                    except Exception as e:
                        print(f"[ChatWolf] Save error: {e}")
            
            for extra_file in existing_files[total_files:]:
                try:
                    os.remove(extra_file)
                except Exception:
                    pass
        
        except Exception as e:
            print(f"[ChatWolf] ❌ Save error: {e}")
        finally:
            is_saving_all_names_data = False


def _save_names_to_file(force=False):
    if is_saving_all_names_data:
        return
    start_save_all_names(force=force).start_threaded()


def _backup_all_names_data() -> None:
    """نسخة احتياطية كل BACKUP_INTERVAL يوم"""
    try:
        config = babase.app.config
        last_backup_str = config.get('CW_LastBackup', '')
        today = datetime.now()
        today_str = today.strftime("%d-%m-%Y")
        
        if last_backup_str:
            try:
                last_backup = datetime.strptime(last_backup_str, "%d-%m-%Y")
                days = (today - last_backup).days
                if days < BACKUP_INTERVAL:
                    return
            except Exception:
                pass
        
        print("[ChatWolf] 📦 Creating backup...")
        backup_name = f"AllNamesBackup_{today_str}"
        archive_path = os.path.join(PlayersBackupDir, backup_name)
        
        try:
            shutil.make_archive(archive_path, 'zip', PlayersDataDir)
            print(f"[ChatWolf] ✅ Backup created: {backup_name}.zip")
        except Exception as e:
            print(f"[ChatWolf] Backup error: {e}")
        
        config['CW_LastBackup'] = today_str
        config.commit()
    
    except Exception as e:
        print(f"[ChatWolf] ❌ Backup error: {e}")


def _update_session_data() -> None:
    """تحديث بيانات اللاعبين من السيرفر"""
    global all_names, current_session_namelist, current_namelist
    
    try:
        roster = bs.get_game_roster() or []
        
        if not roster:
            current_namelist = {}
            return
        
        timestamp = datetime.now().strftime("[%d-%m-%Y | %I:%M %p]")
        new_current = {}
        
        for entry in roster:
            if not isinstance(entry, dict):
                continue
            
            raw_name = entry.get('display_string', '') or ''
            acc_name = _clean_account_name(raw_name)
            if not acc_name:
                acc_name = raw_name.strip()
            if not acc_name:
                continue
            
            players_in_acc = entry.get('players', []) or []
            profiles = []
            for p in players_in_acc:
                if isinstance(p, dict):
                    full_name = p.get('name_full') or p.get('name')
                    if full_name:
                        profiles.append(full_name)
            
            cid = entry.get('client_id')
            if cid is None:
                cid = -1
            
            new_current[acc_name] = {
                'profile_name': profiles,
                'client_id': cid
            }
            
            if acc_name not in current_session_namelist:
                current_session_namelist[acc_name] = {
                    'profile_name': profiles,
                    'client_id': cid
                }
            else:
                old_profiles = current_session_namelist[acc_name].get('profile_name', [])
                if not isinstance(old_profiles, list):
                    old_profiles = []
                combined = list(set(old_profiles + profiles))
                current_session_namelist[acc_name]['profile_name'] = combined
                current_session_namelist[acc_name]['client_id'] = cid
            
            with _data_lock:
                if acc_name not in all_names:
                    all_names[acc_name] = {
                        'profile_name': profiles,
                        'client_id': cid,
                        'last_met': timestamp
                    }
                    print(f"[ChatWolf] 🆕 New player: {acc_name}")
                else:
                    all_names[acc_name]['last_met'] = timestamp
                    if all_names[acc_name].get('client_id') != cid:
                        all_names[acc_name]['client_id'] = cid
                    if profiles:
                        old_p = all_names[acc_name].get('profile_name', [])
                        if not isinstance(old_p, list):
                            old_p = []
                        combined = list(set(old_p + profiles))
                        all_names[acc_name]['profile_name'] = combined
        
        current_namelist = new_current
    
    except Exception as e:
        print(f"[ChatWolf] ❌ Session update error: {e}")


def _get_bcs_player_info(name: str):
    """جيب بيانات اللاعب من Ballistica"""
    global names_asked_bcs
    
    if name not in names_asked_bcs:
        names_asked_bcs.append(name)
    
    try:
        encoded = base64.b64encode(name.encode("utf-8")).decode("utf-8")
        url = f'https://{BALLISTICA_SERVER}/player?key={encoded}&base64=true'
        
        try:
            build_num = _babase.env().get("build_number", 0)
        except Exception:
            build_num = 0
        
        req = urllib.request.Request(url, headers={
            "User-Agent": f'BS{str(build_num)}',
            "Accept-Language": "en-US,en;q=0.9"
        })
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read()
            arr = json.loads(data.decode('utf-8'))
            
            if arr and isinstance(arr, list) and len(arr) > 0:
                names_asked_bcs.remove(name)
                print(f"[ChatWolf] ✅ Got BCS data for: {name}")
                return arr[0]
        
        names_asked_bcs.remove(name)
        print(f"[ChatWolf] ⚠️ No BCS data for: {name}")
        return []
    
    except urllib.error.URLError as e:
        if name in names_asked_bcs:
            names_asked_bcs.remove(name)
        print(f"[ChatWolf] ⚠️ BCS URL error: {e}")
        return None
    
    except Exception as e:
        if name in names_asked_bcs:
            names_asked_bcs.remove(name)
        print(f"[ChatWolf] ❌ BCS error for {name}: {e}")
        return False


def _apply_bcs_data_to_player(name: str, bcs_data: dict) -> None:
    """حفظ بيانات BCS في all_names"""
    global all_names
    
    if not isinstance(bcs_data, dict):
        return
    
    try:
        with _data_lock:
            if name not in all_names:
                all_names[name] = {
                    'profile_name': [],
                    'client_id': '?',
                    'last_met': datetime.now().strftime("[%d-%m-%Y | %I:%M %p]")
                }
            
            player = all_names[name]
            
            pbid = bcs_data.get("pbid")
            if pbid:
                player['pb_id'] = pbid
            
            player_id = bcs_data.get("_id")
            if player_id:
                player['bcs_id'] = player_id
            
            other_accs = bcs_data.get("accounts")
            if other_accs and isinstance(other_accs, list):
                other_accs = [a for a in other_accs if a != name]
                if other_accs:
                    player['other_accounts'] = other_accs
            
            premium_name = bcs_data.get('name')
            if premium_name:
                player['premium_name'] = premium_name
            
            premium_names = bcs_data.get('names')
            if premium_names and isinstance(premium_names, list):
                filtered = [n for n in premium_names if n != premium_name and n != name]
                if filtered:
                    player['other_premium_names'] = filtered
            
            created = bcs_data.get('createdOn')
            if created:
                player['created_on'] = created[:10]
            
            updated = bcs_data.get('updatedOn')
            if updated:
                player['updated_on'] = updated[:10]
            
            discord = bcs_data.get('discord')
            if discord and isinstance(discord, list):
                player['discord'] = discord
            
            char = bcs_data.get('character')
            if char:
                player['spaz'] = char
            
            player['fetched_from_bcs'] = True
        
        print(f"[ChatWolf] 💾 Applied BCS data for: {name}")
    
    except Exception as e:
        print(f"[ChatWolf] ❌ Apply BCS data error: {e}")


def _fetch_player_bcs_async(name: str) -> None:
    """جيب بيانات لاعب في thread منفصل"""
    
    def _worker():
        global _bcs_failed
        
        if _bcs_failed:
            return
        
        if name in _bcs_fetching:
            return
        
        _bcs_fetching.add(name)
        
        try:
            data = _get_bcs_player_info(name)
            
            if data is None:
                _bcs_failed = True
                print(f"[ChatWolf] ⚠️ BCS connection failed — stopping")
                return
            
            if data is False:
                return
            
            if data and isinstance(data, dict):
                _apply_bcs_data_to_player(name, data)
                _save_names_to_file()
            else:
                with _data_lock:
                    if name in all_names:
                        all_names[name]['bcs_searched'] = True
                _save_names_to_file()
        
        except Exception as e:
            print(f"[ChatWolf] ❌ Fetch error for {name}: {e}")
        
        finally:
            if name in _bcs_fetching:
                _bcs_fetching.remove(name)
            if name in names_asked_bcs:
                names_asked_bcs.remove(name)
    
    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def _fetch_all_session_players() -> None:
    """جيب بيانات كل لاعبين الجلسة"""
    global _bcs_failed
    
    if _bcs_failed:
        return
    
    try:
        to_fetch = []
        
        with _data_lock:
            for name, data in current_session_namelist.items():
                if all_names.get(name, {}).get('fetched_from_bcs'):
                    continue
                if all_names.get(name, {}).get('bcs_searched'):
                    continue
                if data.get('client_id') == -1:
                    continue
                
                to_fetch.append(name)
        
        if not to_fetch:
            return
        
        print(f"[ChatWolf] 🌐 Fetching BCS for {len(to_fetch)} player(s)...")
        
        for i, name in enumerate(to_fetch):
            if _bcs_failed:
                break
            _fetch_player_bcs_async(name)
    
    except Exception as e:
        print(f"[ChatWolf] ❌ Fetch all error: {e}")


def _get_my_account_name() -> str:
    """جيب اسم حسابك"""
    try:
        plus = babase.app.plus
        if plus:
            for attr in ["get_v1_account_display_string", "get_account_display_string"]:
                if hasattr(plus, attr):
                    val = getattr(plus, attr)
                    res = val() if callable(val) else val
                    if res and res != "Local":
                        return _clean_account_name(str(res))
    except Exception:
        pass
    return ""


def _send_welcome_message(msg: str) -> None:
    """بيبعت الرسالة من الخيط الرئيسي"""
    try:
        print(f"[ChatWolf] 🔔 Sending welcome: {msg}")
        bs.chatmessage(msg)
    except Exception as e:
        print(f"[ChatWolf] ❌ chatmessage failed: {e}")


def _process_new_players(new_players: set) -> None:
    """معالجة اللاعبين الجداد"""
    try:
        friends = _get_friends_list()
        habibis = _get_habibis_list()
        my_name = _get_my_account_name()
        
        for player in new_players:
            if my_name and player == my_name:
                continue
            
            if player in habibis:
                msg = "❤️ " + player + " joined!"
            elif player in friends:
                msg = "🎉 Welcome back " + player + "!"
            else:
                continue
            
            _send_welcome_message(msg)
    except Exception as e:
        print(f"[ChatWolf] ❌ _process_new_players error: {e}")


def _welcome_watcher_loop() -> None:
    """الخيط الخلفي: بيفحص اللاعبين"""
    global _last_seen_players
    _first_check_done = False
    
    print("[ChatWolf] 🐺 Welcome watcher thread started")
    
    while True:
        try:
            time.sleep(0.5)
            
            if not bs.get_connection_to_host_info_2():
                _last_seen_players = set()
                _first_check_done = False
                continue
            
            roster = bs.get_game_roster() or []
            current = set()
            for entry in roster:
                if not isinstance(entry, dict):
                    continue
                acc = _clean_account_name(entry.get('display_string', ''))
                if acc:
                    current.add(acc)
            
            if not _first_check_done:
                _first_check_done = True
                _last_seen_players = current
                continue
            
            new_players = current - _last_seen_players
            
            if new_players:
                try:
                    _babase.pushcall(
                        babase.CallStrict(_process_new_players, new_players),
                        from_other_thread=True
                    )
                except Exception as e:
                    print(f"[ChatWolf] ❌ pushcall failed: {e}")
                    try:
                        babase.apptimer(
                            0.01,
                            babase.CallStrict(_process_new_players, new_players)
                        )
                    except Exception as e2:
                        print(f"[ChatWolf] ❌ apptimer failed: {e2}")
            
            _last_seen_players = current
            
        except Exception as e:
            print(f"[ChatWolf] ❌ watcher loop error: {e}")
            time.sleep(1.0)


def _start_welcome_watcher() -> None:
    """شغّل الخيط مرة واحدة بس"""
    global _welcome_watcher_started
    if _welcome_watcher_started:
        return
    _welcome_watcher_started = True
    t = threading.Thread(target=_welcome_watcher_loop, daemon=True)
    t.start()
    print("[ChatWolf] ✅ Welcome watcher started")


def _init_player_database() -> None:
    """شغّل نظام قاعدة البيانات"""
    try:
        load_all_names_data()
        Thread(target=_backup_all_names_data, daemon=True).start()
        print("[ChatWolf] 📦 Player database ready")
        
        def _auto_fetch():
            try:
                _fetch_all_session_players()
            except Exception as e:
                print(f"[ChatWolf] Auto fetch error: {e}")
            babase.apptimer(30, babase.CallStrict(_auto_fetch))
        
        babase.apptimer(30, babase.CallStrict(_auto_fetch))
        print("[ChatWolf] ✅ Auto-fetch scheduled")
    
    except Exception as e:
        print(f"[ChatWolf] ❌ Database init error: {e}")


def _open_player_database_window(parent_window=None) -> None:
    """افتح نافذة قاعدة بيانات اللاعبين — نسخة مصغّرة بألوان متناسقة"""
    uiscale = bui.app.ui_v1.uiscale
    
    c_width = 420
    c_height = 480
    
    if parent_window is not None and hasattr(parent_window, '_bg_color'):
        db_bg_color = parent_window._bg_color
    else:
        db_bg_color = babase.app.config.get("PartyWindow_Main_Color", (0.40, 0.55, 0.20))
        if not isinstance(db_bg_color, (list, tuple)) or len(db_bg_color) != 3:
            db_bg_color = (0.40, 0.55, 0.20)
    
    _r, _g, _b = db_bg_color
    btn_primary = (_r * 0.55, _g * 0.75, _b * 0.55)
    btn_secondary = (_r * 0.6, _g * 0.6, _b * 0.6)
    
    cnt = bui.containerwidget(
        scale=(1.6 if uiscale is babase.UIScale.SMALL else
               1.2 if uiscale is babase.UIScale.MEDIUM else 1.0),
        size=(c_width, c_height), transition='in_scale',
        color=db_bg_color,
        parent=bui.get_special_widget('overlay_stack'))
    
    bui.textwidget(parent=cnt, position=(c_width * 0.5, c_height - 25),
        size=(0, 0), h_align='center', v_align='center',
        text='📦 Player Database',
        color=(1, 0.85, 0.2), scale=1.0)
    
    total = len(all_names)
    session_total = len(current_session_namelist)
    bui.textwidget(parent=cnt, position=(c_width * 0.5, c_height - 47),
        size=(0, 0), h_align='center', v_align='center',
        text=f'All: {total}  |  Session: {session_total}',
        color=(0.7, 0.9, 1.0), scale=0.55)
    
    search_field = bui.textwidget(parent=cnt,
        size=(c_width - 25, 32),
        position=(12, c_height - 88),
        text='', editable=True,
        h_align='left', v_align='center',
        description='🔍 Search...',
        autoselect=True, maxwidth=c_width - 35,
        scale=0.65, corner_scale=0.6)
    
    list_h = c_height - 195
    scroll = bui.scrollwidget(parent=cnt,
        size=(c_width - 16, list_h),
        position=(8, 95),
        color=(_r * 0.7, _g * 0.7, _b * 0.7))
    col = bui.columnwidget(parent=scroll, border=0, margin=0)
    
    def _render(players_dict, session_only=False):
        for child in col.get_children():
            child.delete()
        
        if not players_dict:
            bui.textwidget(parent=col,
                size=(c_width - 30, 50),
                position=(0, 0),
                h_align='center', v_align='center',
                text='No players found.',
                color=(0.6, 0.6, 0.6), scale=0.65)
            return
        
        items = list(players_dict.items())
        items.sort(key=lambda x: x[1].get('last_met', ''), reverse=True)
        
        for name, data in items[:300]:
            row = bui.containerwidget(parent=col,
                size=(c_width - 25, 55), background=False)
            
            profiles = data.get('profile_name', [])
            if isinstance(profiles, list):
                profile_str = ', '.join(profiles) if profiles else '(no profile)'
            else:
                profile_str = str(profiles) if profiles else '(no profile)'
            
            cid = data.get('client_id', '?')
            pbid = data.get('pb_id', '')
            
            name_text = f'{name}  [{cid}]'
            if pbid:
                name_text += f'  🆔 {pbid[:12]}...' if len(pbid) > 12 else f'  🆔 {pbid}'
            
            name_color = (0.4, 1, 0.6) if session_only else (1, 0.9, 0.5)
            
            bui.textwidget(parent=row,
                position=((c_width - 25) * 0.5, 42),
                size=(0, 0), h_align='center', v_align='center',
                text=name_text,
                color=name_color, scale=0.58,
                maxwidth=(c_width - 30))
            
            bui.textwidget(parent=row,
                position=((c_width - 25) * 0.5, 25),
                size=(0, 0), h_align='center', v_align='center',
                text=f'👤 {profile_str[:35]}',
                color=(0.8, 0.85, 0.9), scale=0.48,
                maxwidth=(c_width - 30))
            
            discord = data.get('discord', [])
            if discord and isinstance(discord, list):
                discord_str = ', '.join([d.get('username', '?') for d in discord if isinstance(d, dict)])
                if discord_str:
                    bui.textwidget(parent=row,
                        position=((c_width - 25) * 0.5, 10),
                        size=(0, 0), h_align='center', v_align='center',
                        text=f'💬 {discord_str[:30]}',
                        color=(0.7, 0.5, 1.0), scale=0.4,
                        maxwidth=(c_width - 30))
    
    _render(all_names)
    
    def _do_search():
        q = bui.textwidget(query=search_field).strip().lower()
        if not q:
            _render(all_names)
            return
        results = {}
        for name, data in all_names.items():
            if q in name.lower():
                results[name] = data
                continue
            profiles = data.get('profile_name', [])
            if isinstance(profiles, list):
                for p in profiles:
                    if q in str(p).lower():
                        results[name] = data
                        break
        _render(results)
    
    bui.buttonwidget(parent=cnt,
        size=(95, 32), position=(12, 55),
        label='🔍 Search',
        color=btn_primary,
        text_scale=0.6,
        autoselect=True,
        on_activate_call=_do_search)
    
    def _reset():
        bui.textwidget(edit=search_field, text='')
        _render(all_names)
    
    bui.buttonwidget(parent=cnt,
        size=(95, 32), position=(112, 55),
        label='↻ Reset',
        color=btn_secondary,
        text_scale=0.6,
        autoselect=True,
        on_activate_call=_reset)
    
    def _show_session():
        _render(current_session_namelist, session_only=True)
    
    bui.buttonwidget(parent=cnt,
        size=(100, 32), position=(212, 55),
        label='👥 Session',
        color=btn_secondary,
        text_scale=0.6,
        autoselect=True,
        on_activate_call=_show_session)
    
    def _save_now():
        _save_names_to_file(force=True)
        bui.screenmessage('Saving...', color=(0.3, 1, 0.5))
    
    bui.buttonwidget(parent=cnt,
        size=(90, 32), position=(317, 55),
        label='💾 Save',
        color=btn_primary,
        text_scale=0.6,
        autoselect=True,
        on_activate_call=_save_now)
    
    def _close():
        bui.containerwidget(edit=cnt, transition='out_scale')
    
    back_btn = bui.buttonwidget(parent=cnt,
        size=(100, 32), position=(c_width * 0.5 - 50, 15),
        label='Back',
        color=btn_secondary,
        text_scale=0.65,
        autoselect=True,
        on_activate_call=_close)
    
    bui.textwidget(edit=search_field, on_return_press_call=_do_search)
    bui.containerwidget(edit=cnt, cancel_button=back_btn)


# ============================================================
# ========== PARTY WINDOW ==========
# ============================================================

class ChatWolfPartyWindow(bui.Window):
    def __init__(self, *, origin: Sequence[float] = (0, 0)):
        self._uiopenstate = bui.UIOpenState('classicparty')
        self._r = 'partyWindow'
        self.msg_user_selected = ''
        self._popup_type: Optional[str] = None
        self._popup_party_member_client_id: Optional[int] = None
        self._popup_party_member_is_host: Optional[bool] = None
        self._width = 500
        self._popup_party_member_player_id: Optional[int] = None
        self._chat_hist_active = False
        self._chat_hist_index = -1
        self._chat_hist_original = ''
        self._chat_hist_messages = []
        self._caches = {}
        uiscale = bui.app.ui_v1.uiscale
        self._height = (365 if uiscale is babase.UIScale.SMALL else
                        480 if uiscale is babase.UIScale.MEDIUM else 600)
        self._bg_color = babase.app.config.get("PartyWindow_Main_Color", (0.40, 0.55, 0.20)) if not isinstance(
            self._getCustomSets().get("Color"), (list, tuple)) else self._getCustomSets().get("Color")
        if not isinstance(self._bg_color, (list, tuple)) or not len(self._bg_color) == 3:
            self._bg_color = (0.40, 0.55, 0.20)
        bui.Window.__init__(self, root_widget=bui.containerwidget(
            size=(self._width, self._height),
            transition='in_scale', color=self._bg_color,
            parent=bui.get_special_widget('overlay_stack'),
            on_outside_click_call=self.close_with_sound,
            scale_origin_stack_offset=origin,
            scale=(2.0 if uiscale is babase.UIScale.SMALL else
                   1.35 if uiscale is babase.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -10) if uiscale is babase.UIScale.SMALL else (
                240, 0) if uiscale is babase.UIScale.MEDIUM else (330, 20)))
        _r, _g, _b = self._bg_color
        _btn_col  = (_r * 0.8, _g * 0.8, _b * 0.8)
        _btn_col2 = (_r * 0.9, _g * 0.9, _b * 0.9)
        self._cancel_button = bui.buttonwidget(parent=self._root_widget,
            scale=0.7, position=(30, self._height - 47), size=(50, 50),
            label='', on_activate_call=self.close, autoselect=True,
            color=_btn_col, icon=bui.gettexture('crossOut'), iconscale=1.2)
        self._roster_toggle_button = bui.buttonwidget(
            parent=self._root_widget, scale=0.5,
            position=(5, self._height - 47 - 35), size=(50, 40), label='≡',
            on_activate_call=self.roster_mode_changer, autoselect=True,
            color=_btn_col, icon=bui.gettexture('replayIcon'), iconscale=1.0)
        self._ip_button = bui.buttonwidget(
            parent=self._root_widget, scale=0.7,
            position=(-20, self._height - 47 - 85), size=(50, 50), label='IP',
            button_type='square', text_scale=1.2, textcolor=(1, 1, 1),
            on_activate_call=babase.WeakCallStrict(self._on_ip_button_press),
            autoselect=True, color=_btn_col2)
        bui.containerwidget(edit=self._root_widget, cancel_button=self._cancel_button)
        self._menu_button = bui.buttonwidget(
            parent=self._root_widget, scale=0.7,
            position=(self._width - 60, self._height - 47), size=(50, 50),
            label="\xee\x80\x90", autoselect=True, button_type='square',
            on_activate_call=babase.WeakCallStrict(self._on_menu_button_press),
            color=_btn_col2, icon=bui.gettexture('menuButton'), iconscale=1.2)
        self._sorry_button = bui.buttonwidget(
            parent=self._root_widget, scale=0.7, size=(50, 50),
            color=_btn_col2, position=(self._width - 15, self._height - 47 - 50),
            label='sorry', text_scale=0.55, textcolor=(0.3, 1, 0.3),
            button_type='square',
            on_activate_call=babase.WeakCallStrict(self._on_sorry_button_press),
            autoselect=True)
        # ❌ زر Friend اتشال
        info = bs.get_connection_to_host_info_2()
        if info != None:
            if isinstance(info, dict):
                title = info.get("name", "Party")
            else:
                title = getattr(info, "name", "Party")
        else:
            title = babase.Lstr(resource=self._r + '.titleText')
        self._title_text = bui.textwidget(parent=self._root_widget, scale=0.9,
            color=(0.5, 0.7, 0.5), text=title, size=(120, 20),
            position=(self._width * 0.5-60, self._height - 29),
            on_select_call=self.title_selected, selectable=True,
            maxwidth=self._width * 0.7, h_align='center', v_align='center')
        self._empty_str = bui.textwidget(parent=self._root_widget, scale=0.75,
            size=(0, 0), position=(self._width * 0.5, self._height - 65),
            maxwidth=self._width * 0.85, text="no one",
            h_align='center', v_align='center')
        self._scroll_width = self._width - 50
        self._scrollwidget = bui.scrollwidget(parent=self._root_widget,
            size=(self._scroll_width, self._height - 200),
            position=(30, 80), color=(_r*0.7, _g*0.7, _b*0.7))
        self._columnwidget = bui.columnwidget(parent=self._scrollwidget,
            border=2, left_border=-200, margin=0)
        bui.widget(edit=self._menu_button, down_widget=self._columnwidget)
        self._muted_text = bui.textwidget(parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            size=(0, 0), h_align='center', v_align='center', text="")
        self._chat_texts: List[bui.Widget] = []
        self._chat_texts_haxx: List[bui.Widget] = []
        if True:
            msgs = bs.get_chat_messages()
            for msg in msgs:
                self._add_msg(msg, ignore_mute=True)
        self.ping_widget = bui.buttonwidget(
            parent=self._root_widget, scale=0.7, size=(50, 50),
            color=_btn_col2, position=(-20, self._height - 47 - 145),
            label=str(current_ping), text_scale=1.2, textcolor=(0.3, 1, 0.3),
            button_type='square',
            on_activate_call=babase.WeakCallStrict(self._on_ping_button_press),
            selectable=True, autoselect=True)
        _babase.ping_widget = self.ping_widget
        self._id_button = bui.buttonwidget(
            parent=self._root_widget, scale=0.7, size=(50, 50),
            color=_btn_col2, position=(-20, self._height - 47 - 195),
            label='ID', text_scale=0.8, textcolor=(1, 1, 1),
            button_type='square',
            on_activate_call=babase.WeakCallStrict(self._on_id_button_press),
            autoselect=True)
        self._text_field = txt = bui.textwidget(
            parent=self._root_widget, editable=True,
            size=(530-80, 40), position=(44+60, 39),
            text=draft_chat_text, maxwidth=494, shadow=0.3, flatness=1.0,
            description=babase.Lstr(resource=self._r + '.chatMessageText'),
            autoselect=True, v_align='center', corner_scale=0.7)
        bui.widget(edit=self._scrollwidget, autoselect=True,
            left_widget=self._cancel_button, up_widget=self._cancel_button,
            down_widget=self._text_field)
        bui.widget(edit=self._columnwidget, autoselect=True,
            up_widget=self._cancel_button, down_widget=self._text_field)
        bui.containerwidget(edit=self._root_widget, selected_child=txt)
        # ✅ زر Saved Servers
        self._saved_button = bui.buttonwidget(
            parent=self._root_widget,
            size=(30, 30), label='S',
            button_type='square', autoselect=True,
            color=_btn_col,
            textcolor=(1, 1, 1),
            text_scale=1.0,
            position=(self._width - 15, 115),
            on_activate_call=self._open_saved_servers_window)
        # ✅ زر Rejoin
        self._rejoin_button = bui.buttonwidget(
           parent=self._root_widget,
           size=(30, 30), label='',
           button_type='square', autoselect=True,
           color=_btn_col,
           icon=bui.gettexture('replayIcon'),
           iconscale=0.7,
           position=(self._width - 15, 75),
           on_activate_call=self._do_rejoin)
        self._send_button = btn = bui.buttonwidget(parent=self._root_widget,
            size=(50, 35), label=babase.Lstr(resource=self._r + '.sendText'),
            button_type='square', autoselect=True, color=_btn_col2,
            position=(self._width - 70, 35),
            on_activate_call=self._send_chat_message)
        def _times_button_on_click():
            Quickreply = self._get_quick_responds()
            choices = list(Quickreply) + ["__apw_add_quick__", "__apw_remove_quick__"]
            choices_display = _creat_Lstr_list(Quickreply) + [
                _getTransText("Add_a_Quick_Reply", isBaLstr=True),
                _getTransText("Remove_a_Quick_Reply", isBaLstr=True)]
            ChatWolfPopupMenu(position=self._times_button.get_screen_space_center(),
                scale=_get_popup_window_scale(), choices=choices,
                choices_display=choices_display, current_choice=choices[0],
                delegate=self)
            self._popup_type = "QuickMessageSelect"
        self._send_msg_times = 1
        self._times_button = bui.buttonwidget(parent=self._root_widget,
            size=(50, 35), label="Quick", button_type='square',
            autoselect=True, color=_btn_col, position=(30, 35),
            on_activate_call=_times_button_on_click)
        self._hist_up_button = bui.buttonwidget(parent=self._root_widget,
            size=(30, 30), label=babase.charstr(babase.SpecialChar.UP_ARROW),
            position=(-16, 50 + 28), button_type='square', enable_sound=True,
            autoselect=False, color=_btn_col,
            on_activate_call=babase.CallPartial(self._chat_history_step, True))
        self._hist_down_button = bui.buttonwidget(parent=self._root_widget,
            size=(30, 30), label=babase.charstr(babase.SpecialChar.DOWN_ARROW),
            position=(-16, 35), button_type='square', enable_sound=True,
            autoselect=False, color=_btn_col,
            on_activate_call=babase.CallPartial(self._chat_history_step, False))
        bui.textwidget(edit=txt, on_return_press_call=btn.activate)
        self._name_widgets: List[bui.Widget] = []
        self._roster: Optional[List[Dict[str, Any]]] = None
        self.roster_mode = 1
        self.full_chat_mode = False
        self._update_timer = babase.AppTimer(1.0,
            babase.WeakCallStrict(self._update), repeat=True)
        self._update()

    def close_with_sound(self) -> None:
        bui.getsound('swish').play()
        self.close()

    def close(self) -> None:
        global draft_chat_text
        try:
            draft_chat_text = bui.textwidget(query=self._text_field)
        except Exception:
            pass
        try:
            self._update_timer = None
        except Exception:
            pass
        try:
            self._chat_texts_haxx.clear()
        except Exception:
            pass
        try:
            self._name_widgets.clear()
        except Exception:
            pass
        bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def _do_rejoin(self) -> None:
        """يخرج من السيرفر ويدخل تاني"""
        try:
            current_ip = ip_add
            current_port = p_port
            
            if not bs.get_connection_to_host_info_2():
                bui.getsound('error').play()
                bui.screenmessage('Not connected to any server!', color=(1, 0.3, 0.3))
                return
            
            bui.getsound('click01').play()
            bui.screenmessage('⚡ Rejoining...', color=(1, 0.8, 0.2))
            
            try:
                bui.containerwidget(edit=self._root_widget, transition='out_scale')
            except Exception:
                pass
            
            try:
                bs.disconnect_from_host()
            except Exception as e:
                print(f"[ChatWolf] Disconnect error: {e}")
            
            def _reconnect():
                try:
                    newconnect_to_party(current_ip, int(current_port))
                except Exception as e:
                    print(f"[ChatWolf] Rejoin error: {e}")
                    bui.screenmessage(f'Rejoin failed: {e}', color=(1, 0.3, 0.3))
            
            babase.apptimer(1.0, babase.CallStrict(_reconnect))
            
            print(f"[ChatWolf] ⚡ Rejoining {current_ip}:{current_port}")
        
        except Exception as e:
            print(f"[ChatWolf] Rejoin error: {e}")
            bui.screenmessage(f'Rejoin failed: {str(e)}', color=(1, 0.3, 0.3))
            bui.getsound('error').play()

    def title_selected(self):
        self.full_chat_mode = self.full_chat_mode == False
        self._update()

    def roster_mode_changer(self):
        self.roster_mode = (self.roster_mode+1) % 3
        self._update()

    def on_chat_message(self, msg: str) -> None:
        if not self._is_msg_muted(msg):
            self._add_msg(msg)

    def _copy_msg(self, msg: str) -> None:
        if bui.clipboard_is_supported():
            bui.clipboard_set_text(msg)
            bui.screenmessage(bui.Lstr(resource='copyConfirmText'), color=(0, 1, 0))

    def _on_chat_press(self, msg, widget, showMute):
        global unmuted_names
        choices = ['copy', 'reply']
        choices_display = [_getTransText("copymsg", isBaLstr=True),
                          _getTransText("reply", isBaLstr=True)]
        ChatWolfPopupMenu(position=widget.get_screen_space_center(),
            scale=_get_popup_window_scale(), choices=choices,
            choices_display=choices_display, current_choice="copy", delegate=self)
        self.msg_user_selected = msg
        self._popup_type = "chatmessagepress"

    def _is_msg_muted(self, msg: str) -> bool:
        global muted_chat_names
        if not muted_chat_names:
            return False
        sender = msg.split(':', 1)[0].strip()
        def _clean(s):
            result = ''
            for ch in s:
                if not ('\ue000' <= ch <= '\uf8ff'):
                    result += ch
            return result.strip().strip("'")
        sender_clean = _clean(sender)
        for muted in muted_chat_names:
            if sender_clean == _clean(muted):
                return True
        return False

    def _add_msg(self, msg: str, ignore_mute: bool = False) -> None:
        try:
            if not ignore_mute and self._is_msg_muted(msg):
                return
            showMute = babase.app.config.resolve('Chat Muted')
            timestamp = datetime.now().strftime("%I:%M %p")
            msg_with_time = f"[{timestamp}] {msg}"
            txt = bui.textwidget(parent=self._columnwidget, text=msg_with_time,
                h_align='left', v_align='center', size=(900, 13), scale=0.55,
                position=(-0.6, 0), selectable=True, autoselect=True,
                click_activate=True, maxwidth=self._scroll_width * 0.94,
                shadow=0.3, flatness=1.0)
            bui.textwidget(edit=txt, on_activate_call=babase.CallPartial(
                self._on_chat_press, msg, txt, showMute))
            self._chat_texts_haxx.append(txt)
            if len(self._chat_texts_haxx) > 40:
                first = self._chat_texts_haxx.pop(0)
                first.delete()
            bui.containerwidget(edit=self._columnwidget, visible_child=txt)
        except Exception:
            pass

    def color_picker_closing(self, picker) -> None:
        babase._appconfig.commit_app_config()

    def color_picker_selected_color(self, picker, color) -> None:
        bui.containerwidget(edit=self._root_widget, color=color)
        self._bg_color = color
        babase.app.config["PartyWindow_Main_Color"] = color
        r, g, b = color
        btn_color  = (r * 0.8, g * 0.8, b * 0.8)
        btn_color2 = (r * 0.9, g * 0.9, b * 0.9)
        scroll_color = (r * 0.7, g * 0.7, b * 0.7)
        rejoin_color = (r * 0.8, g * 0.8, b * 0.8)
        saved_color = (r * 0.8, g * 0.8, b * 0.8)
        for widget, col in [(self._cancel_button, btn_color),
            (self._roster_toggle_button, btn_color), (self._ip_button, btn_color2),
            (self.ping_widget, btn_color2), (self._id_button, btn_color2),
            (self._menu_button, btn_color2), (self._sorry_button, btn_color2),
            (self._times_button, btn_color),
            (self._hist_up_button, btn_color), (self._hist_down_button, btn_color),
            (self._send_button, btn_color2), (self._rejoin_button, rejoin_color),
            (self._saved_button, saved_color)]:
            try:
                bui.buttonwidget(edit=widget, color=col)
            except Exception:
                pass
        try:
            bui.scrollwidget(edit=self._scrollwidget, color=scroll_color)
        except Exception:
            pass

    def _open_set_nick_window(self, account_id: str) -> None:
        uiscale = bui.app.ui_v1.uiscale
        c_width = 420
        c_height = 200
        cnt = bui.containerwidget(
            scale=(1.6 if uiscale is babase.UIScale.SMALL else
                   1.2 if uiscale is babase.UIScale.MEDIUM else 1.0),
            size=(c_width, c_height), transition='in_scale',
            color=self._bg_color, parent=bui.get_special_widget('overlay_stack'))
        current_nick = self._get_nick(account_id)
        display_nick = '' if current_nick == 'add nick' else current_nick
        bui.textwidget(parent=cnt, position=(c_width * 0.5, c_height - 40),
            size=(0, 0), h_align='center', v_align='center',
            text='Set Nick', color=(1, 0.9, 0.2), scale=0.88,
            maxwidth=c_width * 0.8)
        bui.textwidget(parent=cnt, position=(c_width * 0.5, c_height - 68),
            size=(0, 0), h_align='center', v_align='center',
            text='ID: ' + account_id, color=(0.6, 0.6, 0.6), scale=0.52,
            maxwidth=c_width * 0.85)
        nick_field = bui.textwidget(parent=cnt, size=(c_width - 60, 40),
            position=(30, c_height - 128), text=display_nick, editable=True,
            h_align='left', v_align='center', description='Enter nickname...',
            autoselect=True, max_chars=50, scale=0.75, corner_scale=0.7)
        btn_w = (c_width - 70) // 2
        def _save():
            new_nick = bui.textwidget(query=nick_field)
            config = babase.app.config
            if not isinstance(config.get('players nick'), dict):
                config['players nick'] = {}
            if new_nick.strip():
                config['players nick'][account_id] = new_nick.strip()
                bui.screenmessage("Nick set: " + new_nick.strip(), color=(0.2, 1, 0.4))
            else:
                config['players nick'].pop(account_id, None)
                bui.screenmessage("Nick removed.", color=(1, 0.8, 0.3))
            config.commit()
            bui.containerwidget(edit=cnt, transition='out_scale')
        back_btn = bui.buttonwidget(parent=cnt, size=(btn_w, 42), position=(30, 20),
            label=babase.Lstr(resource='backText', fallback_value='Back'),
            autoselect=True, on_activate_call=babase.CallStrict(
                lambda: bui.containerwidget(edit=cnt, transition='out_scale')))
        save_btn = bui.buttonwidget(parent=cnt, size=(btn_w, 42),
            position=(c_width - btn_w - 30, 20), label='Save',
            color=(0.25, 0.65, 0.25), autoselect=True, on_activate_call=_save)
        bui.textwidget(edit=nick_field, on_return_press_call=_save)
        bui.containerwidget(edit=cnt, cancel_button=back_btn, start_button=save_btn)

    def _get_nick(self, id):
        config = babase.app.config
        if not isinstance(config.get('players nick'), dict):
            return "add nick"
        elif id in config['players nick']:
            return config['players nick'][id]
        else:
            return "add nick"

    def _on_menu_button_press(self) -> None:
        is_muted = babase.app.config.resolve('Chat Muted')
        global chatlogger
        choices = ["unmute" if is_muted else "mute", "screenmsg",
                   "addQuickReply", "removeQuickReply", "chatlogger", "change_color",
                   "player_db", "credits"]
        DisChoices = [_getTransText("unmuteall", isBaLstr=True) if is_muted else _getTransText("muteall", isBaLstr=True),
                      _getTransText("screenmsgoff", isBaLstr=True) if screenmsg else _getTransText("screenmsgon", isBaLstr=True),
                      _getTransText("Add_a_Quick_Reply", isBaLstr=True),
                      _getTransText("Remove_a_Quick_Reply", isBaLstr=True),
                      _getTransText("chatloggeroff", isBaLstr=True) if chatlogger else _getTransText("chatloggeron", isBaLstr=True),
                      _getTransText("change_color", isBaLstr=True),
                      babase.Lstr(resource="??Unknown??", fallback_value="📦 Player Database"),
                      _getTransText("Credits_for_This", isBaLstr=True)]
        if self._getCustomSets().get("Enable_HostInfo_Debug", False):
            choices.append("hostInfo_Debug")
            DisChoices.append(_getTransText("Debug_for_Host_Info", isBaLstr=True))
        ChatWolfPopupMenu(position=self._menu_button.get_screen_space_center(),
            scale=_get_popup_window_scale(), choices=choices,
            choices_display=DisChoices,
            current_choice="unmute" if is_muted else "mute", delegate=self)
        self._popup_type = "menu"

    def _on_party_member_press(self, client_id: int, is_host: bool,
                               widget: bui.Widget) -> None:
        if bs.get_foreground_host_session() is not None:
            kick_str = babase.Lstr(resource="kickText")
        else:
            kick_str = babase.Lstr(resource="kickVoteText")
        global muted_chat_names
        _mute_account = None
        try:
            for entry in (bs.get_game_roster() or []):
                if entry.get('client_id') == client_id:
                    _mute_account = entry.get('display_string', '')
                    break
        except Exception:
            pass
        _is_chat_muted = _mute_account in muted_chat_names if _mute_account else False
        choices = ["@ this guy", "start_kickvote", "kick", "remove", "mute_temp", "ban",
                   "disable_kickvote", "mute_chat", "set_nick"]
        choices_display = [
            _getTransText("Mention_this_guy", isBaLstr=True),
            kick_str,
            babase.Lstr(resource="??Unknown??", fallback_value="Kick - %d" % client_id),
            babase.Lstr(resource="??Unknown??", fallback_value="Remove - %d" % client_id),
            babase.Lstr(resource="??Unknown??", fallback_value="Mute"),
            babase.Lstr(resource="??Unknown??", fallback_value="Ban"),
            babase.Lstr(resource="??Unknown??", fallback_value="KV Disable"),
            babase.Lstr(resource="??Unknown??", fallback_value="Unmute Chat" if _is_chat_muted else "Mute Chat"),
            babase.Lstr(resource="??Unknown??", fallback_value="Set Nick")]
        ChatWolfPopupMenu(position=widget.get_screen_space_center(),
            scale=_get_popup_window_scale(), choices=choices,
            choices_display=choices_display, current_choice="@ this guy", delegate=self)
        self._popup_party_member_client_id = client_id
        self._popup_party_member_is_host = is_host
        self._popup_type = "partyMemberPress"
        self._popup_party_member_player_id = None
        try:
            pids = self._getObjectByID("playerid", ID=client_id)
            if pids:
                if isinstance(pids, (list, tuple)):
                    self._popup_party_member_player_id = pids[0] if pids else None
                else:
                    self._popup_party_member_player_id = pids
        except Exception:
            self._popup_party_member_player_id = None

    def _on_ip_button_press(self) -> None:
        bui.getsound('click01').play()
        bs.chatmessage("joined IP " + ip_add + " PORT " + str(p_port))
        server_name = "Unknown Server"
        try:
            info = bs.get_connection_to_host_info_2()
            if info:
                if isinstance(info, dict):
                    server_name = info.get("name", "Unknown Server") or "Unknown Server"
                else:
                    server_name = getattr(info, "name", "Unknown Server") or "Unknown Server"
        except Exception:
            pass
        bs.chatmessage(str(server_name))

    def _on_ping_button_press(self) -> None:
        if current_ping == 0:
            bs.chatmessage("ping = 0 ms")
        else:
            bs.chatmessage(f"ping = {current_ping} ms")

    def _on_sorry_button_press(self) -> None:
        bs.chatmessage("سوري يحبوب🙂")

    # ⚠️ الدالة _on_friends_button_press لسه موجودة بس مش بتستخدم (الزر اتشال)

    def _open_friends_window(self) -> None:
        """⚠️ النافذة لسه موجودة بس مش بتُستدعى (الزر اتشال)"""
        # الكود كامل زي ما هو، بس مفيش زر بينده عليه
        pass  # ← ممكن تمسحها بالكامل

    def _on_id_button_press(self) -> None:
        try:
            roster = bs.get_game_roster()
            activity = bs.get_foreground_host_activity()
            active_players = []
            if activity:
                active_players = getattr(activity, 'players', []) or []
            active_by_client = {}
            for p in active_players:
                try:
                    cid = p.get_client_id()
                except Exception:
                    cid = None
                if cid is not None:
                    active_by_client[cid] = p
            if not roster and not active_players:
                bui.getsound('error').play()
                bui.screenmessage("لا يوجد لاعبون حالياً", color=(1, 0.5, 0.2))
                return
            collected = []
            seen = set()
            def _clean_uuid(s):
                if not isinstance(s, str):
                    return None
                result = ''
                for ch in s:
                    if not ('\ue000' <= ch <= '\uf8ff'):
                        result += ch
                result = result.strip().strip("'").strip('"')
                if len(result) == 36 and result.count('-') == 4:
                    return result
                return None
            def _clean_name(s):
                if not isinstance(s, str):
                    return ''
                result = ''
                for ch in s:
                    if not ('\ue000' <= ch <= '\uf8ff'):
                        result += ch
                return result.strip().strip("'").strip('"')
            for entry in roster:
                if not isinstance(entry, dict):
                    continue
                client_id = entry.get('client_id', '?')
                display = entry.get('display_string', '') or ''
                players = entry.get('players', []) or []
                active_player = active_by_client.get(client_id)
                uuid_val = None
                if active_player:
                    try:
                        account_id = active_player.get_account_id()
                        if account_id:
                            uuid_val = account_id
                    except Exception:
                        pass
                if not uuid_val:
                    uuid_val = _clean_uuid(display)
                if not uuid_val:
                    uuid_val = ""
                if active_player:
                    try:
                        pname = active_player.getname()
                    except Exception:
                        pname = display
                    try:
                        p_id = active_player.get_id()
                    except Exception:
                        p_id = None
                    state = "IN GAME"
                    if p_id is not None:
                        key = f"{client_id}_{uuid_val}_{p_id}_{pname}"
                        if key not in seen:
                            seen.add(key)
                            collected.append({'client_id': client_id,
                                'uuid': uuid_val, 'ppid': p_id, 'name': pname,
                                'state': state, 'account': display})
                elif players:
                    for pl in players:
                        pl_name = pl.get('name_full', pl.get('name', '?'))
                        pl_id = pl.get('id', None)
                        if pl_id is None:
                            continue
                        key = f"{client_id}_{uuid_val}_{pl_id}_{pl_name}"
                        if key not in seen:
                            seen.add(key)
                            collected.append({'client_id': client_id,
                                'uuid': uuid_val, 'ppid': pl_id, 'name': pl_name,
                                'state': "IN LOBBY", 'account': display})
            if not collected:
                bui.getsound('error').play()
                bui.screenmessage("فشل جلب ال uuid", color=(1, 0.5, 0.2))
                return
            bui.screenmessage(
                f"Fetching PB-IDs for {len(collected)} player(s)...",
                color=(0.5, 0.8, 1))
            results = {'done': 0, 'total': len(collected), 'items': []}
            def _on_each_done(idx, pbid):
                results['done'] += 1
                item = collected[idx].copy()
                item['pbid'] = pbid if pbid else 'N/A'
                results['items'].append((idx, item))
                if results['done'] >= results['total']:
                    results['items'].sort(key=lambda x: x[0])
                    final_items = [i[1] for i in results['items']]
                    choices = []
                    for it in final_items:
                        label = (f"| {it['client_id']} | {it['pbid']} | "
                                f"{it['account']} | {it['state']} |")
                        choices.append(label)
                    if not choices:
                        bui.screenmessage("No valid players found.", color=(1, 0.5, 0.2))
                        return
                    ChatWolfPopupMenu(
                        position=self._id_button.get_screen_space_center(),
                        scale=_get_popup_window_scale(), choices=choices,
                        choices_display=choices, current_choice=choices[0],
                        delegate=self)
                    self._popup_type = "id_select"
            for idx, item in enumerate(collected):
                clean_name = _clean_name(item['account']) or _clean_name(item['name'])
                _fetch_pbid_async(clean_name, lambda pbid, i=idx: _on_each_done(i, pbid))
        except Exception as e:
            bui.getsound('error').play()
            bui.screenmessage("فشل جلب اللاعبين: " + str(e), color=(1, 0.3, 0.3))

    def _chat_history_step(self, back: bool) -> None:
        msgs = bs.get_chat_messages()
        if not msgs:
            bui.getsound('block').play()
            bui.screenmessage("Empty chat", color=(1, 0.5, 0.2))
            return
        if not self._chat_hist_active:
            self._chat_hist_original = bui.textwidget(query=self._text_field)
            self._chat_hist_messages = msgs
            self._chat_hist_active = True
            self._chat_hist_index = len(msgs) if back else -1
        self._chat_hist_index += -1 if back else 1
        if self._chat_hist_index < 0:
            self._chat_hist_index = -1
            self._chat_hist_active = False
            bui.textwidget(edit=self._text_field, text=self._chat_hist_original)
            bui.getsound('deek').play()
            return
        if self._chat_hist_index >= len(self._chat_hist_messages):
            self._chat_hist_index = len(self._chat_hist_messages) - 1
            bui.getsound('deek').play()
            return
        try:
            raw = self._chat_hist_messages[self._chat_hist_index]
            text = raw.split(": ", 1)[1] if ": " in raw else raw
        except Exception:
            text = self._chat_hist_messages[self._chat_hist_index]
        bui.textwidget(edit=self._text_field, text=text)
        bui.textwidget(edit=self._text_field, select_all=True)
        bui.getsound('deek').play()
            def _send_chat_message(self) -> None:
        global draft_chat_text
        self._chat_hist_active = False
        sendtext = bui.textwidget(query=self._text_field)
        if sendtext == ".ip":
            bs.chatmessage("joined "+ip_add+" PORT "+str(p_port))
            bui.textwidget(edit=self._text_field, text="")
            return
        elif sendtext == ".info":
            if bs.get_connection_to_host_info_2() == None:
                s_build = 0
            else:
                s_build = bs.get_connection_to_host_info_2()['build_number']
            s_v = "0"
            if s_build <= 14365:
                s_v = " 1.4.148 or below"
            elif s_build <= 14377:
                s_v = "1.4.148 < x < = 1.4.155 "
            elif s_build >= 20001 and s_build < 20308:
                s_v = "1.5"
            elif s_build >= 20308 and s_build < 20591:
                s_v = "1.6 "
            else:
                s_v = "1.7 and above "
            bs.chatmessage("script version "+s_v+"- build "+str(s_build))
            bui.textwidget(edit=self._text_field, text="")
            return
        elif sendtext == ".ping":
            if current_ping == 0:
                bs.chatmessage("Ping: N/A (server unreachable)")
            else:
                bs.chatmessage(f"My ping: {current_ping} ms")
            bui.textwidget(edit=self._text_field, text="")
            return
        elif sendtext == ".save":
            info = bs.get_connection_to_host_info_2()
            config = babase.app.config
            if info != None and info.get('name', '') != '':
                title = info['name']
                if not isinstance(config.get('Saved Servers'), dict):
                    config['Saved Servers'] = {}
                config['Saved Servers'][f'{ip_add}@{p_port}'] = {
                    'addr': ip_add, 'port': p_port, 'name': title}
                config.commit()
                bs.broadcastmessage("Server saved to manual")
                bui.getsound('gunCocking').play()
                bui.textwidget(edit=self._text_field, text="")
                return
        if '\\' in sendtext:
            sendtext = sendtext.replace('\\d', ('\ue048'))
            sendtext = sendtext.replace('\\c', ('\ue043'))
            sendtext = sendtext.replace('\\h', ('\ue049'))
            sendtext = sendtext.replace('\\s', ('\ue046'))
            sendtext = sendtext.replace('\\n', ('\ue04b'))
            sendtext = sendtext.replace('\\f', ('\ue04f'))
            sendtext = sendtext.replace('\\g', ('\ue027'))
            sendtext = sendtext.replace('\\i', ('\ue03a'))
            sendtext = sendtext.replace('\\m', ('\ue04d'))
            sendtext = sendtext.replace('\\t', ('\ue01f'))
            sendtext = sendtext.replace('\\bs', ('\ue01e'))
            sendtext = sendtext.replace('\\j', ('\ue010'))
            sendtext = sendtext.replace('\\e', ('\ue045'))
            sendtext = sendtext.replace('\\l', ('\ue047'))
            sendtext = sendtext.replace('\\a', ('\ue020'))
            sendtext = sendtext.replace('\\b', ('\ue00c'))
        if sendtext == "":
            sendtext = "   "
        msg = sendtext
        msg1 = msg.split(" ")
        ms2 = ""
        if (len(msg1) > 11):
            hp = int(len(msg1)/2)
            for m in range(0, hp):
                ms2 = ms2+" "+msg1[m]
            bs.chatmessage(ms2)
            ms2 = ""
            for m in range(hp, len(msg1)):
                ms2 = ms2+" "+msg1[m]
            bs.chatmessage(ms2)
        else:
            bs.chatmessage(msg)

    def _get_quick_responds(self):
        if not hasattr(self, "_caches") or not isinstance(self._caches, dict):
            self._caches = {}
        try:
            filePath = os.path.join(RecordFilesDir, "Quickmessage.txt")
            if os.path.exists(RecordFilesDir) is not True:
                os.makedirs(RecordFilesDir)
            if not os.path.isfile(filePath):
                with open(filePath, "wb") as writer:
                    writer.write(("/custom3 210 add  permanent\\n/thawall\\n/maxPlayers 15\\n/par l\\n"
                                 "/par spark 123 size=3\\n/lm\\n/give srounder_chef\\n/quit\\n/sm\\n"
                                 "/end\\n/admin 153 add permanent").encode("UTF-8"))
            if os.path.getmtime(filePath) != self._caches.get("Vertify_Quickresponse_Text"):
                with open(filePath, "r+", encoding="utf-8") as Reader:
                    Text = Reader.read()
                    if Text.startswith(str(codecs.BOM_UTF8)):
                        Text = Text[3:]
                    self._caches["quickReplys"] = (Text).split("\\n")
                    self._caches["Vertify_Quickresponse_Text"] = os.path.getmtime(filePath)
            return (self._caches.get("quickReplys", []))
        except Exception:
            babase.print_exception()
            bs.broadcastmessage(babase.Lstr(resource="errorText"), (1, 0, 0))
            bui.getsound("error").play()

    def _write_quick_responds(self, data):
        try:
            with open(os.path.join(RecordFilesDir, "Quickmessage.txt"), "wb") as writer:
                writer.write("\\n".join(data).encode("utf-8"))
        except Exception:
            babase.print_exception()
            bs.broadcastmessage(babase.Lstr(resource="errorText"), (1, 0, 0))
            bui.getsound("error").play()

    def _getCustomSets(self):
        try:
            if not hasattr(self, "_caches") or not isinstance(self._caches, dict):
                self._caches = {}
            try:
                from VirtualHost import MainSettings
                if MainSettings.get("Custom_PartyWindow_Sets", {}) != self._caches.get("PartyWindow_Sets", {}):
                    self._caches["PartyWindow_Sets"] = MainSettings.get("Custom_PartyWindow_Sets", {})
            except Exception:
                try:
                    filePath = os.path.join(RecordFilesDir, "Settings.json")
                    if os.path.isfile(filePath):
                        if os.path.getmtime(filePath) != self._caches.get("Vertify_MainSettings.json_Text"):
                            with open(filePath, "r+", encoding="utf-8") as Reader:
                                Text = Reader.read()
                                if Text.startswith(str(codecs.BOM_UTF8)):
                                    Text = Text[3:]
                                self._caches["PartyWindow_Sets"] = json.loads(
                                    Text.decode("utf-8")).get("Custom_PartyWindow_Sets", {})
                            self._caches["Vertify_MainSettings.json_Text"] = os.path.getmtime(filePath)
                except Exception:
                    babase.print_exception()
            return (self._caches.get("PartyWindow_Sets") if isinstance(
                self._caches.get("PartyWindow_Sets"), dict) else {})
        except Exception:
            babase.print_exception()

    def _getObjectByID(self, type="playerName", ID=None):
        if ID is None:
            ID = self._popup_party_member_client_id
        type = type.lower()
        output = []
        for roster in self._roster:
            if type.startswith("all"):
                if type in ("roster", "fullrecord"):
                    output += [roster]
                elif type.find("player") != -1 and roster["players"] != []:
                    if type.find("namefull") != -1:
                        output += [(i["name_full"]) for i in roster["players"]]
                    elif type.find("name") != -1:
                        output += [(i["name"]) for i in roster["players"]]
                    elif type.find("playerid") != -1:
                        output += [i["id"] for i in roster["players"]]
                elif type.lower() in ("account", "displaystring"):
                    output += [(roster["display_string"])]
            elif roster["client_id"] == ID and not type.startswith("all"):
                try:
                    if type in ("roster", "fullrecord"):
                        return (roster)
                    elif type.find("player") != -1 and roster["players"] != []:
                        if len(roster["players"]) == 1 or type.find("singleplayer") != -1:
                            if type.find("namefull") != -1:
                                return ((roster["players"][0]["name_full"]))
                            elif type.find("name") != -1:
                                return ((roster["players"][0]["name"]))
                            elif type.find("playerid") != -1:
                                return (roster["players"][0]["id"])
                        else:
                            if type.find("namefull") != -1:
                                return ([(i["name_full"]) for i in roster["players"]])
                            elif type.find("name") != -1:
                                return ([(i["name"]) for i in roster["players"]])
                            elif type.find("playerid") != -1:
                                return ([i["id"] for i in roster["players"]])
                    elif type.lower() in ("account", "displaystring"):
                        return ((roster["display_string"]))
                except Exception:
                    babase.print_exception()
        return (None if len(output) == 0 else output)

    def _edit_text_msg_box(self, text, type="rewrite"):
        if not isinstance(type, str) or not isinstance(text, str):
            return
        type = type.lower()
        text = (text)
        if type.find("add") != -1:
            bui.textwidget(edit=self._text_field,
                text=bui.textwidget(query=self._text_field)+text)
        else:
            bui.textwidget(edit=self._text_field, text=text)

    def _get_saved_servers(self) -> list:
        config = babase.app.config
        servers = config.get('APW_Saved_Servers', [])
        if not isinstance(servers, list):
            servers = []
        return servers

    def _write_saved_servers(self, servers: list) -> None:
        babase.app.config['APW_Saved_Servers'] = servers
        babase.app.config.commit()

    def _open_saved_servers_window(self) -> None:
        uiscale = bui.app.ui_v1.uiscale
        servers = self._get_saved_servers()
        c_width = 500
        row_h = 72
        header_h = 55
        footer_h = 62
        list_h = min(len(servers) * row_h + 10, 360) if servers else 70
        c_height = header_h + list_h + footer_h
        cnt = bui.containerwidget(
            scale=(1.6 if uiscale is babase.UIScale.SMALL else
                   1.2 if uiscale is babase.UIScale.MEDIUM else 1.0),
            size=(c_width, c_height), transition='in_scale',
            color=self._bg_color, parent=bui.get_special_widget('overlay_stack'))
        bui.textwidget(parent=cnt, position=(c_width * 0.5, c_height - 28),
            size=(0, 0), h_align='center', v_align='center',
            text='Saved Servers', color=(1, 0.85, 0.2), scale=0.95,
            maxwidth=c_width * 0.85)
        scroll = bui.scrollwidget(parent=cnt, size=(c_width - 16, list_h),
            position=(8, footer_h + 8))
        col = bui.columnwidget(parent=scroll, border=2, margin=0)
        for i, srv in enumerate(servers):
            srv_name = srv.get('name', 'Unnamed')
            srv_addr = srv.get('addr', '?')
            srv_port = srv.get('port', 43210)
            rh = 80
            rw = c_width - 20
            btn_w = 80
            btn_h = 28
            btn_x = rw - btn_w - 6
            gap = 6
            join_y = rh - 6 - btn_h
            rem_y = join_y - btn_h - gap
            row = bui.containerwidget(parent=col, size=(rw, rh), background=False)
            text_w = rw - btn_w - 18
            bui.textwidget(parent=row, position=(8, rh - 26), size=(0, 0),
                h_align='left', v_align='center', text=srv_name,
                color=(1, 1, 0.7), scale=0.65, maxwidth=text_w)
            bui.textwidget(parent=row, position=(8, rh - 50), size=(0, 0),
                h_align='left', v_align='center',
                text='IP: %s   Port: %s' % (srv_addr, srv_port),
                color=(0.7, 0.88, 1.0), scale=0.54, maxwidth=text_w)
            def _join(addr=srv_addr, port=srv_port, c=cnt):
                bui.containerwidget(edit=c, transition='out_scale')
                newconnect_to_party(addr, int(port))
            bui.buttonwidget(parent=row, size=(btn_w, btn_h),
                position=(btn_x, join_y), label='Join', color=(0.2, 0.65, 0.3),
                autoselect=True, on_activate_call=_join)
            def _delete(idx=i, c=cnt):
                svrs = self._get_saved_servers()
                if 0 <= idx < len(svrs):
                    svrs.pop(idx)
                    self._write_saved_servers(svrs)
                bui.containerwidget(edit=c, transition='out_scale')
                self._open_saved_servers_window()
            bui.buttonwidget(parent=row, size=(btn_w, btn_h),
                position=(btn_x, rem_y), label='Remove',
                color=(0.65, 0.15, 0.15), autoselect=True,
                on_activate_call=_delete)
        if not servers:
            bui.textwidget(parent=col, size=(c_width - 24, 60),
                position=(0, 0), h_align='center', v_align='center',
                text='No saved servers yet.', color=(0.6, 0.6, 0.6),
                scale=0.62, maxwidth=c_width - 40)
        btn_y = 10
        btn_w = 148
        gap = (c_width - btn_w * 3) // 4
        bui.buttonwidget(parent=cnt, size=(btn_w, 42), position=(gap, btn_y),
            label='+ Add Server', color=(0.25, 0.55, 0.8), autoselect=True,
            on_activate_call=babase.CallPartial(self._open_add_server_window, cnt))
        def _add_this_server():
            info = bs.get_connection_to_host_info_2()
            if not info:
                bui.screenmessage('Not connected to any server!', color=(1, 0.3, 0.3))
                bui.getsound('error').play()
                return
            if isinstance(info, dict):
                srv_name = info.get('name', 'Unknown')
                srv_addr = info.get('addr', info.get('address', ''))
                srv_port = info.get('port', 43210)
            else:
                srv_name = getattr(info, 'name', 'Unknown')
                srv_addr = getattr(info, 'addr', getattr(info, 'address', ''))
                srv_port = getattr(info, 'port', 43210)
            if not srv_addr:
                bui.screenmessage('Could not get server address!', color=(1, 0.3, 0.3))
                bui.getsound('error').play()
                return
            svrs = self._get_saved_servers()
            for s in svrs:
                if s.get('addr') == srv_addr and s.get('port') == srv_port:
                    bui.screenmessage('Server already saved!', color=(1, 0.8, 0.2))
                    bui.getsound('error').play()
                    return
            svrs.append({'name': srv_name, 'addr': srv_addr, 'port': int(srv_port)})
            self._write_saved_servers(svrs)
            bui.getsound('gunCocking').play()
            bui.screenmessage("'%s' saved!" % srv_name, color=(0.2, 1, 0.4))
            bui.containerwidget(edit=cnt, transition='out_scale')
            self._open_saved_servers_window()
        bui.buttonwidget(parent=cnt, size=(btn_w, 42),
            position=(gap * 2 + btn_w, btn_y), label='+ This Server',
            color=(0.2, 0.6, 0.4), autoselect=True, on_activate_call=_add_this_server)
        cancel_btn = bui.buttonwidget(parent=cnt, size=(btn_w, 42),
            position=(gap * 3 + btn_w * 2, btn_y),
            label=babase.Lstr(resource='backText', fallback_value='Back'),
            autoselect=True, on_activate_call=babase.CallStrict(
                lambda: bui.containerwidget(edit=cnt, transition='out_scale')))
        bui.containerwidget(edit=cnt, cancel_button=cancel_btn)

    def _open_add_server_window(self, parent_cnt=None) -> None:
        uiscale = bui.app.ui_v1.uiscale
        c_width = 420
        c_height = 290
        if parent_cnt is not None:
            try:
                bui.containerwidget(edit=parent_cnt, transition='out_scale')
            except Exception:
                pass
        cnt = bui.containerwidget(
            scale=(1.75 if uiscale is babase.UIScale.SMALL else
                   1.3 if uiscale is babase.UIScale.MEDIUM else 1.0),
            size=(c_width, c_height), transition='in_scale',
            color=self._bg_color, parent=bui.get_special_widget('overlay_stack'))
        bui.textwidget(parent=cnt, position=(c_width * 0.5, c_height - 28),
            size=(0, 0), h_align='center', v_align='center',
            text='Add Server', color=(1, 0.85, 0.2), scale=0.9,
            maxwidth=c_width * 0.85)
        field_w = c_width - 80
        lbl_color = (0.75, 0.88, 1.0)
        lbl_scale = 0.62
        bui.textwidget(parent=cnt, position=(40, c_height - 68), size=(0, 0),
            h_align='left', v_align='center', text='Server Name:',
            color=lbl_color, scale=lbl_scale)
        name_field = bui.textwidget(parent=cnt, size=(field_w, 36),
            position=(40, c_height - 108), text='', editable=True,
            description='e.g. My Fav Server', h_align='left', v_align='center',
            autoselect=True, maxwidth=field_w - 10, max_chars=40,
            scale=0.65, corner_scale=0.7)
        bui.textwidget(parent=cnt, position=(40, c_height - 138), size=(0, 0),
            h_align='left', v_align='center', text='IP Address:',
            color=lbl_color, scale=lbl_scale)
        ip_field = bui.textwidget(parent=cnt, size=(field_w, 36),
            position=(40, c_height - 178), text='', editable=True,
            description='e.g. 192.168.1.1', h_align='left', v_align='center',
            autoselect=True, maxwidth=field_w - 10, max_chars=64,
            scale=0.65, corner_scale=0.7)
        bui.textwidget(parent=cnt, position=(40, c_height - 205), size=(0, 0),
            h_align='left', v_align='center', text='Port:',
            color=lbl_color, scale=lbl_scale)
        port_field = bui.textwidget(parent=cnt, size=(120, 36),
            position=(40, c_height - 245), text='43210', editable=True,
            description='e.g. 43210', h_align='left', v_align='center',
            autoselect=True, maxwidth=110, max_chars=6, scale=0.65,
            corner_scale=0.7)
        def _save():
            srv_name = bui.textwidget(query=name_field).strip()
            srv_addr = bui.textwidget(query=ip_field).strip()
            srv_port_str = bui.textwidget(query=port_field).strip()
            if not srv_addr:
                bui.screenmessage('IP address cannot be empty!', color=(1, 0.3, 0.3))
                bui.getsound('error').play()
                return
            try:
                srv_port = int(srv_port_str)
            except ValueError:
                bui.screenmessage('Port must be a number!', color=(1, 0.3, 0.3))
                bui.getsound('error').play()
                return
            if not srv_name:
                srv_name = '%s:%d' % (srv_addr, srv_port)
            servers = self._get_saved_servers()
            for s in servers:
                if s.get('addr') == srv_addr and s.get('port') == srv_port:
                    bui.screenmessage('Server already saved!', color=(1, 0.8, 0.2))
                    bui.getsound('error').play()
                    return
            servers.append({'name': srv_name, 'addr': srv_addr, 'port': srv_port})
            self._write_saved_servers(servers)
            bui.getsound('gunCocking').play()
            bui.screenmessage("Server '%s' saved!" % srv_name, color=(0.2, 1, 0.4))
            bui.containerwidget(edit=cnt, transition='out_scale')
            self._open_saved_servers_window()
        save_btn = bui.buttonwidget(parent=cnt, size=(160, 44),
            position=(c_width * 0.5 - 85, 12), label='Save',
            color=(0.25, 0.65, 0.3), autoselect=True, on_activate_call=_save)
        cancel_btn = bui.buttonwidget(parent=cnt, size=(100, 44),
            position=(c_width * 0.5 + 85, 12),
            label=babase.Lstr(resource='backText', fallback_value='Back'),
            autoselect=True, on_activate_call=babase.CallStrict(
                lambda: bui.containerwidget(edit=cnt, transition='out_scale')))
        bui.containerwidget(edit=cnt, cancel_button=cancel_btn, start_button=save_btn)
        bui.widget(edit=name_field, down_widget=ip_field)
        bui.widget(edit=ip_field, down_widget=port_field)
        bui.widget(edit=port_field, down_widget=save_btn)
        bui.textwidget(edit=port_field, on_return_press_call=save_btn.activate)

    def _open_credits_window(self) -> None:
        uiscale = bui.app.ui_v1.uiscale
        c_width = 420
        c_height = 220
        cnt = bui.containerwidget(
            scale=(1.7 if uiscale is babase.UIScale.SMALL else
                   1.3 if uiscale is babase.UIScale.MEDIUM else 1.0),
            size=(c_width, c_height), transition='in_scale',
            color=self._bg_color, parent=bui.get_special_widget('overlay_stack'))
        bui.textwidget(parent=cnt, position=(c_width * 0.5, c_height - 28),
            size=(0, 0), h_align='center', v_align='center',
            text='CHATT WOLF', color=(1, 0.85, 0.2), scale=0.95,
            maxwidth=c_width * 0.85)
        bui.textwidget(parent=cnt, position=(c_width * 0.5, c_height - 60),
            size=(0, 0), h_align='center', v_align='center',
            text='Version 1.11', color=(0.3, 1, 0.3), scale=0.62,
            maxwidth=c_width * 0.85)
        bui.textwidget(parent=cnt, position=(c_width * 0.5, c_height - 90),
            size=(0, 0), h_align='center', v_align='center',
            text='BY NOVO', color=(0.7, 0.9, 1.0), scale=0.62,
            maxwidth=c_width * 0.85)
        bui.textwidget(parent=cnt, position=(c_width * 0.5, c_height - 118),
            size=(0, 0), h_align='center', v_align='center',
            text='discord.gg/CScj4tauz', color=(0.55, 0.75, 1.0), scale=0.58,
            maxwidth=c_width * 0.85)
        bui.textwidget(parent=cnt, position=(c_width * 0.5, c_height - 140),
            size=(0, 0), h_align='center', v_align='center',
            text='─' * 38, color=(0.35, 0.45, 0.35), scale=0.45,
            maxwidth=c_width * 0.9)
        btn_y = 14
        btn_h = 44
        btn_w = 175
        padding = 12
        back_btn = bui.buttonwidget(parent=cnt, size=(btn_w, btn_h),
            position=(padding, btn_y), label=babase.Lstr(resource='backText'),
            autoselect=True, on_activate_call=babase.CallStrict(
                lambda: bui.containerwidget(edit=cnt, transition='out_scale')))
        bui.buttonwidget(parent=cnt, size=(btn_w, btn_h),
            position=(c_width - btn_w - padding, btn_y),
            label='Join Our Discord', color=(0.3, 0.4, 0.8),
            autoselect=True, on_activate_call=self.joinbombspot)
        bui.containerwidget(edit=cnt, cancel_button=back_btn)

    def joinbombspot(self):
        bui.open_url("https://discord.gg/CScj4tauz")

    def _update(self) -> None:
        try:
            if current_ping == 0:
                bui.buttonwidget(edit=self.ping_widget, label="0")
            else:
                bui.buttonwidget(edit=self.ping_widget, label=str(current_ping))
        except Exception:
            pass
        roster = bs.get_game_roster()
        global f_chat, smo_mode
        if roster != self._roster or smo_mode != self.roster_mode or f_chat != self.full_chat_mode:
            self._roster = roster
            smo_mode = self.roster_mode
            f_chat = self.full_chat_mode
            for widget in self._name_widgets:
                widget.delete()
            self._name_widgets = []
            if not self._roster:
                top_section_height = 60
                bui.textwidget(edit=self._empty_str,
                    text=babase.Lstr(resource=self._r + '.emptyText'))
                bui.scrollwidget(edit=self._scrollwidget,
                    size=(self._width - 50, self._height - top_section_height - 110),
                    position=(30, 80))
            elif self.full_chat_mode:
                top_section_height = 60
                bui.scrollwidget(edit=self._scrollwidget,
                    size=(self._width - 50, self._height - top_section_height - 75),
                    position=(30, 80))
            else:
                columns = 1 if len(self._roster) == 1 else 2 if len(self._roster) == 2 else 3
                rows = int(math.ceil(float(len(self._roster)) / columns))
                c_width = (self._width * 0.9) / max(3, columns)
                c_width_total = c_width * columns
                c_height = 24
                c_height_total = c_height * rows
                for y in range(rows):
                    for x in range(columns):
                        index = y * columns + x
                        if index < len(self._roster):
                            t_scale = 0.65
                            pos = (self._width * 0.53 - c_width_total * 0.5 +
                                   c_width * x - 23,
                                   self._height - 65 - c_height * y - 15)
                            try:
                                if self.roster_mode == 1 and self._roster[index]['players']:
                                    if len(self._roster[index]['players']) == 1:
                                        p_str = self._roster[index]['players'][0]['name_full']
                                    else:
                                        p_str = ('/'.join([entry['name'] for entry in
                                                          self._roster[index]['players']]))
                                        if len(p_str) > 25:
                                            p_str = p_str[:25] + '...'
                                elif self.roster_mode == 0:
                                    p_str = self._roster[index]['display_string']
                                    p_str = self._get_nick(p_str)
                                else:
                                    p_str = self._roster[index]['display_string']
                            except Exception:
                                p_str = '???'
                            try:
                                widget = bui.textwidget(parent=self._root_widget,
                                    position=(pos[0], pos[1]), scale=t_scale,
                                    size=(c_width * 0.85, 30),
                                    maxwidth=c_width * 0.85,
                                    color=(1, 1, 1) if index == 0 else (1, 1, 1),
                                    selectable=True, autoselect=True,
                                    click_activate=True,
                                    text=babase.Lstr(value=p_str),
                                    h_align='left', v_align='center')
                                self._name_widgets.append(widget)
                            except Exception:
                                pass
                            if self._roster[index]['client_id'] is not None:
                                is_host = self._roster[index]['client_id'] == -1
                            else:
                                is_host = (index == 0)
                            try:
                                bui.textwidget(edit=widget,
                                    on_activate_call=babase.CallPartial(
                                        self._on_party_member_press,
                                        self._roster[index]['client_id'],
                                        is_host, widget))
                            except Exception:
                                pass
                            pos = (self._width * 0.53 - c_width_total * 0.5 +
                                   c_width * x,
                                   self._height - 65 - c_height * y)
                            if is_host:
                                twd = min(c_width * 0.85,
                                    _babase.get_string_width(p_str,
                                        suppress_warning=True) * t_scale)
                                try:
                                    self._name_widgets.append(
                                        bui.textwidget(parent=self._root_widget,
                                            position=(pos[0] + twd + 1, pos[1] - 0.5),
                                            size=(0, 0), h_align='left',
                                            v_align='center',
                                            maxwidth=c_width * 0.96 - twd,
                                            color=(0.1, 1, 0.1, 0.5),
                                            text=babase.Lstr(resource=self._r + '.hostText'),
                                            scale=0.4, shadow=0.1, flatness=1.0))
                                except Exception:
                                    pass
                try:
                    bui.textwidget(edit=self._empty_str, text='')
                    bui.scrollwidget(edit=self._scrollwidget,
                        size=(self._width - 50,
                              max(100, self._height - 139 - c_height_total)),
                        position=(30, 80))
                except Exception:
                    pass
        try:
            _update_session_data()
        except Exception as e:
            print(f"[ChatWolf] Update session error: {e}")

    def hide_screen_msg(self):
        try:
            with open('ba_data/data/languages/english.json', encoding='utf-8') as file:
                eng = json.loads(file.read())
            eng['internal']['playerJoinedPartyText'] = ''
            eng['internal']['playerLeftPartyText'] = ''
            eng['internal']['chatBlockedText'] = ''
            eng['kickVoteStartedText'] = ''
            eng['kickWithChatText'] = ''
            eng['kickOccurredText'] = ''
            eng['kickVoteFailedText'] = ''
            eng['votesNeededText'] = ''
            eng['playerDelayedJoinText'] = ''
            eng['playerLeftText'] = ''
            eng['kickQuestionText'] = ''
            with open('ba_data/data/languages/english.json', 'w', encoding='utf-8') as file:
                json.dump(eng, file)
        except Exception:
            pass
        def _reload():
            try:
                lang = babase.app.config.get('Lang', 'English') or 'English'
                bs.app.lang.setlanguage(lang)
            except RuntimeError:
                pass
        bui.apptimer(0.5, _reload)

    def restore_screen_msg(self):
        try:
            with open('ba_data/data/languages/english.json', encoding='utf-8') as file:
                eng = json.loads(file.read())
            eng['internal']['playerJoinedPartyText'] = "${NAME} joined the pawri!"
            eng['internal']['playerLeftPartyText'] = "${NAME} left the pawri."
            eng['internal']['chatBlockedText'] = "${NAME} is chat-blocked for ${TIME} seconds."
            eng['kickVoteStartedText'] = "A kick vote has been started for ${NAME}."
            eng['kickWithChatText'] = "Type ${YES} in chat for yes and ${NO} for no."
            eng['kickOccurredText'] = "${NAME} was kicked."
            eng['kickVoteFailedText'] = "Kick-vote failed."
            eng['votesNeededText'] = "${NUMBER} votes needed"
            eng['internal']['playerDelayedJoinText'] = "${PLAYER} will enter at the start of the next round."
            eng['internal']['playerLeftText'] = "${PLAYER} left the game."
            eng['internal']['kickQuestionText'] = "Kick ${NAME}?"
            with open('ba_data/data/languages/english.json', 'w', encoding='utf-8') as file:
                json.dump(eng, file)
        except Exception:
            pass
        def _reload():
            try:
                lang = babase.app.config.get('Lang', 'English') or 'English'
                bs.app.lang.setlanguage(lang)
            except RuntimeError:
                pass
        bui.apptimer(0.5, _reload)

    def popup_menu_selected_choice(self, popup_window, choice: str) -> None:
        global unmuted_names
        if self._popup_type == "QuickMessageSelect":
            if choice == "__apw_add_quick__":
                try:
                    newReply = bui.textwidget(query=self._text_field)
                    if newReply:
                        data = self._get_quick_responds()
                        data.append(newReply)
                        self._write_quick_responds(data)
                        bs.broadcastmessage(_getTransText("Something_is_added") %
                                            newReply, color=(0, 1, 0))
                        bui.getsound("dingSmallHigh").play()
                    else:
                        bui.getsound("error").play()
                except Exception:
                    babase.print_exception()
                return
            elif choice == "__apw_remove_quick__":
                Quickreply = self._get_quick_responds()
                if len(Quickreply) > 0:
                    ChatWolfPopupMenu(position=self._times_button.get_screen_space_center(),
                        scale=_get_popup_window_scale(), choices=Quickreply,
                        choices_display=_creat_Lstr_list(Quickreply),
                        current_choice=Quickreply[0], delegate=self)
                    self._popup_type = "removeQuickReplySelect"
                else:
                    bui.getsound("error").play()
                return
            try:
                self._edit_text_msg_box(choice, "rewrite")
                try:
                    bui.containerwidget(edit=self._root_widget,
                        selected_child=self._text_field)
                except Exception:
                    pass
            except Exception:
                babase.print_exception()
        elif self._popup_type == "MentionSelect":
            try:
                self._edit_text_msg_box(choice + ' ', "add")
                try:
                    bui.containerwidget(edit=self._root_widget,
                        selected_child=self._text_field)
                except Exception:
                    pass
            except Exception:
                babase.print_exception()
        elif self._popup_type == "removeQuickReplySelect":
            try:
                data = self._get_quick_responds()
                if choice in data:
                    data.remove(choice)
                    self._write_quick_responds(data)
                    bs.broadcastmessage(
                        _getTransText("Something_is_removed", same_fb=True) % choice
                        if "%s" in _getTransText("Something_is_removed", same_fb=True)
                        else '"%s" removed' % choice, color=(1, 0.5, 0))
                    bui.getsound("dingSmallHigh").play()
            except Exception:
                babase.print_exception()
        elif self._popup_type == "banTimePress":
            result = _babase.disconnect_client(
                self._popup_party_member_client_id, ban_time=int(choice))
            if not result:
                bui.getsound('error').play()
                bs.broadcastmessage(
                    babase.Lstr(resource='getTicketsWindow.unavailableText'),
                    color=(1, 0, 0))
        elif self._popup_type == "banDurationPress":
            ban_time = int(choice)
            try:
                if ban_time == 0:
                    cmd = "/ban %d" % self._popup_party_member_client_id
                else:
                    cmd = "/ban %d %d" % (self._popup_party_member_client_id, ban_time)
                bs.chatmessage(cmd)
            except Exception:
                bui.getsound('error').play()
                babase.print_exception()
        elif self._popup_type == "muteDurationPress":
            mute_seconds = int(choice)
            try:
                if mute_seconds == 0:
                    cmd = "/mute %d" % self._popup_party_member_client_id
                else:
                    cmd = "/mute %d %d" % (self._popup_party_member_client_id, mute_seconds)
                bs.chatmessage(cmd)
            except Exception:
                bui.getsound('error').play()
                babase.print_exception()
        elif self._popup_type == "send_Times_Press":
            pass
        elif self._popup_type == "chatmessagepress":
            if choice == "mute":
                unmuted_names.remove(self.msg_user_selected.split(":")[0].encode('utf-8'))
            if choice == "unmute":
                unmuted_names.append(self.msg_user_selected.split(":")[0].encode('utf-8'))
            if choice == "copy":
                self._copy_msg(self.msg_user_selected)
            if choice == "reply":
                parts = self.msg_user_selected.split(":", 1)
                sender = parts[0].strip()
                msg_body = parts[1].strip() if len(parts) > 1 else ""
                words = msg_body.split()
                trimmed = " ".join(words[:3]) + ("..." if len(words) > 3 else "")
                reply_text = "@%s %s " % (sender, trimmed)
                self._edit_text_msg_box(reply_text, "rewrite")
                try:
                    bui.containerwidget(edit=self._root_widget,
                        selected_child=self._text_field)
                except Exception:
                    pass
        elif self._popup_type == "partyMemberPress":
            if choice == "start_kickvote":
                result = bs.disconnect_client(self._popup_party_member_client_id, ban_time=0)
                if not result:
                    bui.getsound('error').play()
                    bs.broadcastmessage(
                        babase.Lstr(resource='getTicketsWindow.unavailableText'),
                        color=(1, 0, 0))
            elif choice == "kick":
                bs.chatmessage("/kick %d" % self._popup_party_member_client_id)
            elif choice == "remove":
                player_id = getattr(self, '_popup_party_member_player_id', None)
                if player_id is not None:
                    bs.chatmessage("/remove %d" % player_id)
            elif choice == "ban":
                account = self._getObjectByID("account")
                if account:
                    bs.chatmessage(f"/idban {account}")
            elif choice == "mute_temp":
                self._popup_type = "muteDurationPress"
                mute_choices = [1, 10, 20, 50, 100, 0]
                mute_labels = [str(s) for s in mute_choices[:-1]] + ["Permanent"]
                ChatWolfPopupMenu(
                    position=self.get_root_widget().get_screen_space_center(),
                    scale=_get_popup_window_scale(),
                    choices=[str(s) for s in mute_choices],
                    choices_display=_creat_Lstr_list(mute_labels),
                    current_choice=str(mute_choices[0]), delegate=self)
            elif choice == "disable_kickvote":
                bs.chatmessage("/kickvote disable %d" % self._popup_party_member_client_id)
                bs.broadcastmessage(_getTransText("kickvote_disabled", same_fb=True),
                                    color=(0.5, 1, 1))
            elif choice == "mute_chat":
                global muted_chat_names
                account = self._getObjectByID("account")
                if account:
                    if account in muted_chat_names:
                        muted_chat_names.discard(account)
                        try:
                            player_names = self._getObjectByID("playerNameFull")
                            if isinstance(player_names, str):
                                muted_chat_names.discard(player_names)
                            elif isinstance(player_names, list):
                                for n in player_names:
                                    muted_chat_names.discard(n)
                        except Exception:
                            pass
                        bs.broadcastmessage("Chat unmuted: %s" % account,
                                            color=(0.5, 1, 0.5))
                    else:
                        muted_chat_names.add(account)
                        try:
                            player_names = self._getObjectByID("playerNameFull")
                            if isinstance(player_names, str):
                                muted_chat_names.add(player_names)
                            elif isinstance(player_names, list):
                                for n in player_names:
                                    if n:
                                        muted_chat_names.add(n)
                        except Exception:
                            pass
                        bs.broadcastmessage("Chat muted: %s" % account,
                                            color=(1, 0.7, 0.3))
            elif choice == "set_nick":
                account = self._getObjectByID("account")
                if account:
                    self._open_set_nick_window(account)
                else:
                    bui.screenmessage("Could not get player ID.", color=(1, 0.3, 0.3))
            elif choice == "@ this guy":
                NameChoices = []
                account = self._getObjectByID("account")
                if account and account not in NameChoices:
                    NameChoices.append(account)
                temp = self._getObjectByID("playerNameFull")
                if temp is not None:
                    if isinstance(temp, str) and temp not in NameChoices:
                        NameChoices.append(temp)
                    elif isinstance(temp, (list, tuple)):
                        for item in temp:
                            if isinstance(item, str) and item not in NameChoices:
                                NameChoices.append(item)
                nick = self._get_nick(account) if account else None
                if nick and nick != 'add nick' and nick not in NameChoices:
                    NameChoices.append(nick)
                if not NameChoices:
                    bui.getsound('error').play()
                    bs.broadcastmessage(
                        _getTransText("No_valid_player_found", same_fb=True),
                        color=(1, 0, 0))
                else:
                    ChatWolfPopupMenu(
                        position=popup_window.root_widget.get_screen_space_center(),
                        scale=_get_popup_window_scale(), choices=NameChoices,
                        choices_display=_creat_Lstr_list(NameChoices),
                        current_choice=NameChoices[0], delegate=self)
                    self._popup_type = "MentionSelect"
        elif self._popup_type == "menu":
            if choice in ("mute", "unmute"):
                cfg = babase.app.config
                cfg['Chat Muted'] = (choice == 'mute')
                cfg.apply_and_commit()
                if cfg['Chat Muted']:
                    customchatThread().run()
                self._update()
            elif choice in ("credits",):
                self._open_credits_window()
            elif choice == "player_db":
                _open_player_database_window(self)
            elif choice == "chatlogger":
                global chatlogger
                if chatlogger:
                    chatlogger = False
                    bs.broadcastmessage("Chat logger turned OFF")
                else:
                    chatlogger = True
                    chatloggThread().run()
                    bs.broadcastmessage("Chat logger turned ON")
            elif choice == "change_color":
                ColorPickerExact(parent=self.get_root_widget(),
                    position=self.get_root_widget().get_screen_space_center(),
                    initial_color=self._bg_color, delegate=self, tag='')
            elif choice == "saved_servers":
                self._open_saved_servers_window()
            elif choice == 'screenmsg':
                global screenmsg
                if screenmsg:
                    screenmsg = False
                    self.hide_screen_msg()
                else:
                    screenmsg = True
                    self.restore_screen_msg()
            elif choice == "addQuickReply":
                try:
                    newReply = bui.textwidget(query=self._text_field)
                    data = self._get_quick_responds()
                    data.append(newReply)
                    self._write_quick_responds(data)
                    bs.broadcastmessage(_getTransText("Something_is_added") %
                                        newReply, color=(0, 1, 0))
                    bui.getsound("dingSmallHigh").play()
                except Exception:
                    babase.print_exception()
            elif choice == "removeQuickReply":
                Quickreply = self._get_quick_responds()
                ChatWolfPopupMenu(
                    position=self._text_field.get_screen_space_center(),
                    scale=_get_popup_window_scale(), choices=Quickreply,
                    choices_display=_creat_Lstr_list(Quickreply),
                    current_choice=Quickreply[0], delegate=self)
                self._popup_type = "removeQuickReplySelect"
        elif self._popup_type == "id_select":
            try:
                bs.chatmessage(choice)
            except Exception:
                pass

# ba_meta export babase.Plugin

class ChatWolfPlugin(babase.Plugin):
    def __init__(self):
        try:
            bs.connect_to_party = newconnect_to_party
            bascenev1lib_party.PartyWindow = ChatWolfPartyWindow
            babase.apptimer(3.0, _init_player_database)
            babase.apptimer(8.0, self._start_update_check)
            babase.apptimer(10.0, lambda: start_new_thread(_send_usage_ping, ()))
            babase.apptimer(5.0, _start_welcome_watcher)
        except Exception:
            babase.print_exception("[APW] Plugin init crashed — attempting self-repair …")
            self._self_repair()

    def _start_update_check(self):
        start_new_thread(_apw_check_and_update, ())

    def _self_repair(self):
        if _apw_restore_backup():
            try:
                babase.screenmessage(
                    "Chatt Wolf: crash detected, restored backup. Please restart.",
                    color=(1, 0.8, 0.2))
            except Exception:
                pass
            return
        def _repair_thread():
            ok = _apw_download_update("crash-repair")
            def _notify():
                try:
                    if ok:
                        babase.screenmessage(
                            "Chatt Wolf: crash repaired from GitHub! Please restart.",
                            color=(0.2, 1, 0.4))
                    else:
                        babase.screenmessage(
                            "Chatt Wolf: repair failed. Check console.",
                            color=(1, 0.3, 0.3))
                except Exception:
                    pass
            try:
                _babase.pushcall(_notify, from_other_thread=True)
            except Exception:
                pass
        start_new_thread(_repair_thread, ())

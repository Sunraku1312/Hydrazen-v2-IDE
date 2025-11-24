import winreg
import subprocess
import os
import shutil

ICO_NAME = "hydrazen_icone.ico"
EXT = ".Hydra2"
FILE_TYPE = "Hydra2file"

script_dir = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(script_dir, ICO_NAME)

def set_reg(root, path, name, value):
    key = winreg.CreateKey(root, path)
    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
    winreg.CloseKey(key)

def delete_userchoice():
    path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\%s\UserChoice" % EXT
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
        print("Clé UserChoice supprimée.")
    except FileNotFoundError:
        print("Pas de UserChoice → rien à supprimer.")
    except PermissionError:
        print("Impossible de supprimer UserChoice (Windows protège la clé).")
        print("Lance le script en administrateur.")

if not os.path.isfile(ICON_PATH):
    print("Icône introuvable :", ICON_PATH)
    exit()

print("➡ Icône utilisée :", ICON_PATH)

delete_userchoice()

set_reg(winreg.HKEY_CLASSES_ROOT, EXT, "", FILE_TYPE)

set_reg(winreg.HKEY_CLASSES_ROOT, f"{FILE_TYPE}\\DefaultIcon", "", ICON_PATH)

set_reg(winreg.HKEY_CLASSES_ROOT, FILE_TYPE, "", "Hydra2 File")

print("Redémarrage de l'explorateur...")
subprocess.run(["taskkill", "/f", "/im", "explorer.exe"])
subprocess.Popen("explorer.exe")

print("Icône appliquée avec succès !")

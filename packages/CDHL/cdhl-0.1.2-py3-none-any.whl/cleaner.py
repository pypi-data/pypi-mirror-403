from pathlib import Path
import shutil

# main function to group all important objects together
def chdl():
    # downloads folder path
    home_path = Path.home()
    downloads_folder = home_path / "Downloads/demo"
    images_folder = home_path / "Pictures/demo"
    audio_folder = home_path / "Music/demo"
    videos_folder = home_path / "Videos/demo"
    documents_folder = home_path / "Documents/demo"
    begin_operation(downloads_folder, images_folder, audio_folder, videos_folder, documents_folder, home_path)


# classifies file type by extension and decides where to put it
def begin_sorting(item, images_folder, audio_folder, videos_folder, documents_folder, home_path, dry_run = True):
    # lists of extensions
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma', '.aiff', '.opus'}
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.mpeg', '.mpg', '.3gp'}
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.tiff', '.tif', '.heic', '.heif', '.ico', '.raw', '.cr2', '.nef'}
    document_extensions = {'.txt', '.rtf', '.doc', '.docx', '.odt', '.pdf', '.xls', '.xlsx', '.xlsm', '.ods', '.csv', '.ppt', '.pptx', '.odp', '.key', '.epub', '.mobi', '.azw', '.azw3', '.md', '.markdown', '.tex', '.log', '.xml', '.json', '.yaml', '.yml', '.pages', '.numbers', '.dotx', '.xltx', '.potx', '.wps', '.wpd', '.ott', '.ots', '.otp'}
    app_extensions = {'.exe', '.msi', '.app', '.dmg', '.pkg', '.deb', '.rpm', '.apk', '.ipa', '.jar', '.bin', '.run', '.appimage', '.snap', '.flatpak', '.iso', '.img', '.vhd', '.vmdk', '.ova', '.dll', '.so', '.dylib', '.sys', '.bat', '.sh', '.command', '.ps1', '.vbs', '.wsf', '.gadget', '.appx', '.msix'}
    archive_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tgz', '.tbz2', '.tar.gz', '.tar.bz2', '.tar.xz', '.cab', '.arj', '.lzh', '.ace', '.zoo', '.arc', '.pak', '.z', '.lz', '.lzma', '.tlz', '.war', '.ear', '.jar', '.deb', '.rpm', '.dmg', '.iso', '.img', '.sit', '.sitx', '.sea', '.zipx'}
    miscellaneous_extensions = {'.tmp', '.temp', '.bak', '.old', '.cache', '.crdownload', '.part', '.download', '.torrent', '.lnk', '.url', '.webloc', '.desktop', '.ini', '.cfg', '.conf', '.dat', '.db', '.sqlite', '.plist', '.reg', '.swp', '.swo', '.DS_Store', '.thumbs.db', '.localized', '.nfo', '.diz', '.me', '.1st', '.log', '.dump', '.crash', '.core', '.lock', '.pid'}

    # print dry run results
    if dry_run:
        if item.suffix in audio_extensions:
            print(f"{item.name} will be moved to {audio_folder}")
        elif item.suffix in video_extensions:
            print(f"{item.name} will be moved to {videos_folder}")
        elif item.suffix in image_extensions:
            print(f"{item.name} will be moved to {images_folder}")
        elif item.suffix in document_extensions:
            print(f"{item.name} will be moved to {documents_folder}")
        elif item.suffix in app_extensions:
            print(f"{item.name} will be moved to {home_path} / Applications")
        elif item.suffix in miscellaneous_extensions:
            print(f"{item.name} will be moved to {home_path} / Miscellaneous")
        elif item.suffix in archive_extensions:
            print(f"{item.name} will be moved to {home_path} / Archive")
        else:
            print(f"{item.name} will be moved to {home_path} / Other")

    # sort items based on extensions
    if not dry_run:
        try:
            if item.suffix in audio_extensions:
                shutil.move(item, audio_folder)
            elif item.suffix in video_extensions:
                shutil.move(item, videos_folder)
            elif item.suffix in image_extensions:
                shutil.move(item, images_folder)
            elif item.suffix in document_extensions:
                shutil.move(item, documents_folder)
            elif item.suffix in app_extensions:
                app_directory = home_path / "Applications"
                app_directory.mkdir(parents=True, exist_ok=True)
                shutil.move(item, app_directory)
            elif item.suffix in miscellaneous_extensions:
                misc_directory = home_path / "Miscellaneous"
                misc_directory.mkdir(parents=True, exist_ok=True)
                shutil.move(item, misc_directory)
            elif item.suffix in archive_extensions:
                archive_directory = home_path / "Archive"
                archive_directory.mkdir(parents=True, exist_ok=True)
                shutil.move(item, archive_directory)
            else:
                other_directory = home_path / "Other"
                other_directory.mkdir(parents=True, exist_ok=True)
                shutil.move(item, other_directory)
        except FileNotFoundError:
            print(f"Sorry {item.name} was not found.")
        except PermissionError:
            print("Permission denied")
        except OSError:
            print("OS error occurred")
        except Exception as e:
            print(f"Unexpected error: {e}")



# scans items in folder on the go. generator good since me not know how big user's downloads folder is
def scan_folder_generator(downloads_folder):
    for item in downloads_folder.iterdir():
        yield item
        # scans recursively. will comment for now for easier testing and debugging.
        # add this advanced feature when basic tool is complete
        #if item.is_dir():
        #    yield from scan_folder_generator(item)

#
def begin_operation(downloads_folder, images_folder, audio_folder, videos_folder, documents_folder, home_path):
    for item in scan_folder_generator(downloads_folder):
        begin_sorting(item, images_folder, audio_folder, videos_folder, documents_folder, home_path, dry_run=True)

    # users confirm sorting operation
    confirm_sorting = input("Begin sorting? y/n: ")

    if confirm_sorting == "y":
        for item in scan_folder_generator(downloads_folder):
            begin_sorting(item, images_folder, audio_folder, videos_folder, documents_folder, home_path, dry_run=False)




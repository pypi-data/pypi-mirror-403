# CDHL

CDHL (Clean Drive Happy Life) is a Python utility that automatically organizes files in your Downloads folder by file type, with a dry-run preview before making any changes.

## Features

- **Dry Run Preview** - See what changes will be made before actually moving files
- **Proper Categorization** - Automatically sorts files into appropriate folders:
  - Images (~/Pictures)
  - Audio (~/Music)
  - Videos (~Videos)
  - Documents (~/Documents)
  - Applications (~/Applications)
  - Archives (~/Archive)
  - Miscellaneous (~/Miscellaneous)
  - Other (~/Other)
- **Efficient Processing** - Uses generators for memory-efficient handling of large directories
- **Safe Operation** - Requires user confirmation before moving files
- **Comprehensive File Type Support** - Recognizes 100+ file extensions across all major categories

## Installation

```bash
pip install CDHL
```

## Usage

```python
from cleaner import chdl

# Run the file organizer
chdl()
```

The tool will:
1. Scan your Downloads folder
2. Show a preview of where each file will be moved
3. Ask for confirmation
4. Move files to their appropriate destinations

### Supported File Types

- **Images**: jpg, jpeg, png, gif, webp, bmp, svg, tiff, heic, raw, and more
- **Audio**: mp3, wav, flac, aac, ogg, opus, and more
- **Videos**: mp4, mov, avi, mkv, webm, mpeg, and more
- **Documents**: pdf, doc, docx, txt, xlsx, ppt, csv, epub, and more
- **Applications**: exe, msi, app, dmg, apk, jar, and more
- **Archives**: zip, rar, 7z, tar, gz, iso, and more

## Example Output

```
example_photo.jpg will be moved to /Users/username/Pictures
song.mp3 will be moved to /Users/username/Music
video.mp4 will be moved to /Users/username/Videos
document.pdf will be moved to /Users/username/Documents

Begin sorting? y/n:
```

## Requirements

- Python 3.9+
- No external dependencies (uses only standard library)

## Safety Features

- All operations show a preview before execution
- User must explicitly confirm file movements
- Graceful error handling for missing files, permission issues, and OS errors
- Creates destination folders automatically if they don't exist

## Development

This project uses Hatchling as the build backend.

### Building

```bash
python -m build
```


## Future Enhancements

- Recursive folder scanning
- Custom categorization rules
- Configuration file support
- Undo functionality
- Duplicate file handling

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Mon G.

## Changelog

### 0.1.0 (Initial Release)
- Basic file organization by type
- Dry run preview functionality
- User confirmation before file movement
- Support for 100+ file extensions
# xclean

File de-duplication utility.

Scan files in main to record main files to compare against.

Scan files in target to find files that are duplicates of those in main.

By default it just lists the duplicates.

## Removing duplicates

Specify --remove to actually remove the duplicate files.

## Archiving duplicates

Specify --archive-to to archive the duplicate files to another location.

## Archiving new files

Specify --archive-new to archive any new files to another location.

## Trashing duplicates

Specify --trash to move the duplicate files to the trash.

## Reset the database

Reset the database content of main files by specifying --clean.

## Compare XMP files as well

To compare the file and associated XMP file specify the --xmp option as well.

## Compare AAE files as well

To compare the file and associated AAE file specify the --aae option as well.

## Scanning specific file types

To scan files of specific types use the --include and --exclude options.

## Prompt before changing

To answer a prompt before changing a file specify --prompt

## Installation

### Using pypi

    pip install xclean

### Using github

    pip install https://github.com/bbc6502/xclean/archive/refs/heads/main.zip

## Usage

    usage: xclean [-h] [--main MAIN] [--target TARGET] [--archive-to ARCHIVE_TO] 
              [--archive-new ARCHIVE_NEW] [--import-new IMPORT_NEW] [-i [INCLUDE ...]]
              [-x [EXCLUDE ...]] [--exclude-dir [EXCLUDE_DIR ...]] [--unprotect] 
              [--remove] [--trash] [--clean] [--xmp] [--aae] [--prompt] [--new] [--dup]
              [--summary] [--copy] [--ignore-existing] [--minsize MINSIZE]

    options:
      -h, --help            show this help message and exit
      --main MAIN           Directory where main files reside
      --target TARGET       Directory where duplicate files may reside
      --archive-to ARCHIVE_TO
                            Archive duplicates to directory
      --archive-new ARCHIVE_NEW
                            Archive new files to directory
      --import-new IMPORT_NEW
                            Directory where to import new main files into
      -i [INCLUDE ...], --include [INCLUDE ...]
                            Include Extensions
      -x [EXCLUDE ...], --exclude [EXCLUDE ...]
                            Exclude Extensions
      --exclude-dir [EXCLUDE_DIR ...]
                            Exclude directories
      --unprotect           Unprotect main files
      --remove              Remove duplicate files
      --trash               Trash duplicate files
      --clean               Clean database
      --xmp                 Include xmp files when checking for duplicates
      --aae                 Include aae files when checking for duplicates
      --prompt              Prompt before making changes
      --new                 Report new files
      --dup                 Report duplicate files
      --summary             Report summary of changes
      --copy                Copy files instead of moving
      --ignore-existing     Ignore existing archive files
      --minsize MINSIZE     Minimum size to clean

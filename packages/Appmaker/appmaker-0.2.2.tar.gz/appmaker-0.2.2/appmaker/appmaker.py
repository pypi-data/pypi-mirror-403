from sys import argv
import os
from platform import platform


def main():
    # Help Message
    def help_str():
        print("Create an app from an Binary!\n\nUsage: appmaker [script] [--options]"
              "\n\nOptions:\n"
              "   -n or --name for the name of the app\n"
              "   -i or --icon for an icon file (must be .icns\n"
              "   -a or --author for an author\n"
              "   -v or --version for a version number (must be a string)\n\n"
              "Example: appmaker ./main.py --name \"My App\" --icon \"./assets/icon.icns\" --author \"Pixel Master\" "
              "--version \"1.0\"\n\n "
              "appmaker -h or appmaker --help for this page")

    # Function for building.app
    def build_app():
        # Name
        if "-n" in argv or "--name" in argv:
            if "-n" in argv:
                name = argv[argv.index("-n") + 1]
            else:
                name = argv[argv.index("--name") + 1]
        else:
            name = os.path.basename(argv[1])
        pure_name = name
        name = f"{name}.app"

        # Icon
        if "-i" in argv or "--icon" in argv:
            if "-i" in argv:
                icon = argv[argv.index("-i") + 1]
            else:
                icon = argv[argv.index("--icon") + 1]
            if not os.path.exists(icon):
                raise OSError("Item path is wrong")
        else:
            icon = None

        # Author
        if "-a" in argv or "--author" in argv:
            if "-a" in argv:
                author = argv[argv.index("-a") + 1]
            else:
                author = argv[argv.index("--author") + 1]
        else:
            author = os.path.basename(os.path.expanduser("~"))

        # Version
        if "-v" in argv or "--version" in argv:
            if "-v" in argv:
                version = argv[argv.index("-v") + 1]
            else:
                version = argv[argv.index("--version") + 1]
        else:
            version = "1.0"

        # Constructing.app
        # Creating dirs
        maindir = os.path.join(name, "Contents")
        macosdir = os.path.join(maindir, "MacOS")
        ressourcedir = os.path.join(maindir, "Resources")

        os.makedirs(maindir, exist_ok=True)
        os.makedirs(macosdir, exist_ok=True)
        os.makedirs(ressourcedir, exist_ok=True)

        # Copying Binary
        with open(argv[1], "rb") as BinaryFile:
            Binary = BinaryFile.read()
        with open(os.path.join(macosdir, pure_name), "wb") as BinaryFileCopy:
            BinaryFileCopy.write(Binary)
        os.system("chmod +x " + os.path.join(macosdir, pure_name).replace(" ", "\ "))

        # Copying Icon
        if icon is not None:
            with open(icon, "rb") as IconFile:
                IconBinary = IconFile.read()
            with open(os.path.join(ressourcedir, "Icon.icns"), "wb") as IconFileCopy:
                IconFileCopy.write(IconBinary)

        del Binary

        # Creating info.plist
        with open(os.path.join(maindir, "Info.plist"), "w") as infofile:
            infofile.write(f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
                           f"\n<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
                           f"\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> "
                           f"\n<plist version=\"1.0\">"
                           f"\n<dict>"
                           f"\n    <key>CFBundleAllowMixedLocalizations</key>"
                           f"\n    <true/>"
                           f"\n    <key>CFBundleExecutable</key>"
                           f"\n    <string>{pure_name}</string>"
                           f"\n    <key>CFBundleIconFile</key>"
                           f"\n    <string>Icon</string>"
                           f"\n    <key>CFBundleIconName</key>"
                           f"\n    <string>Icon</string>"
                           f"\n    <key>CFBundleShortVersionString</key>"
                           f"\n    <string>{version}</string>"
                           f"\n    <key>NSHumanReadableCopyright</key>"
                           f"\n    <string>{author}</string>"
                           f"\n</dict>"
                           f"\n</plist>")

    # Help Message
    if "-h" in argv or "--help" in argv:
        help_str()
    # create .app
    elif platform() != "darwin":
        try:
            if os.path.exists(argv[1]):
                build_app()
            else:
                print(f"No Binary found under: {argv[1]}\n\nBinary must be first argument!")
        except IndexError:
            help_str()
            print("\n\nYou need to include a binary!")
    else:
        print("appmaker only supports macOS at the moment!\nFeel free to contribute!")

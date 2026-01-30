from py2gui import display, user_type_in, run, clear, copy_text, select_all, exit_gui, user_write, display_colored, display_paragraph

def main():
    display_colored("Welcome to the Py2GUI Test Application!", fg_color="34", bold=True)  # Blue bold text
    display("Hello, world!")
    
    name = user_type_in("Enter your name:  ")
    display(f"Hi {name}!")
    display("This is a test.")
    
    if user_type_in("type clear to clear  ") == "clear":
        clear()
    else:
        display("You didn't clear")
        if user_type_in("type copy to copy last line  ") == "copy":
            copy_text()
            display("Last line copied to clipboard.")
            user_write("So btw... how are you feeling?  ")
        else:
            display("You didn't copy")
            display("This is some \033[1;32mgreen bold text\033[0m and this is \033[1;31mred bold text\033[0m.")
    
    display("Select all text and copy it manually to see select_all in action.")
    
    if user_type_in("type select_all to select all text   ") == "select_all":
        select_all()
        display("All text selected.")
        if user_type_in("type copy to copy all selected text  ") == "copy":
            copy_text()
            display("All text copied to clipboard.")
    else:
        display("You didn't select all")

    display("=== display_colored Method Demo ===")
    display_colored("Blue text", fg_color="34")
    display_colored("Red background", bg_color="41")
    display_colored("Bold green", fg_color="32", bold=True)
    display_colored("Underlined yellow", fg_color="33", underline=True)
    display_colored("Italic cyan", fg_color="36", italic=True)
    display_colored("Bold white on red", fg_color="37", bg_color="41", bold=True)
    
    display("=== display_paragraph Demo ===")
    display_paragraph("This is a paragraph that spans\\nmultiple lines.\\t\\tIt has tabs too!")
    display_paragraph("No newline at the end of this one")
    display("This adds a newline after the paragraph")
    
    display("=== Font Demo ===")
    display("Default font", parse_ansi=False)
    display("Arial font", font_family="Arial", parse_ansi=False)
    display("Helvetica bold", font_family="Helvetica", font_style="bold", parse_ansi=False)
    
    display("=== ANSI Color Terminal Demo ===", parse_ansi=False)
    display("")
    
    # Basic colors
    display("Basic ANSI Colors:")
    display("\033[30mBlack\033[0m \033[31mRed\033[0m \033[32mGreen\033[0m \033[33mYellow\033[0m")
    display("\033[34mBlue\033[0m \033[35mMagenta\033[0m \033[36mCyan\033[0m \033[37mWhite\033[0m")
    display("")
    
    # Bright colors
    display("Bright Colors:")
    display("\033[90mGray\033[0m \033[91mBright Red\033[0m \033[92mBright Green\033[0m")
    display("\033[93mBright Yellow\033[0m \033[94mBright Blue\033[0m \033[95mBright Magenta\033[0m")
    display("")
    
    # Background colors
    display("Background Colors:")
    display("\033[40;37mBlack Background\033[0m \033[41mRed Background\033[0m")
    display("\033[42mGreen Background\033[0m \033[43mYellow Background\033[0m")
    display("")
    
    # Text styles
    display("Text Styles:")
    display("\033[1mBold\033[0m \033[3mItalic\033[0m \033[4mUnderline\033[0m \033[9mStrikethrough\033[0m")
    display("")
    
    # Combined styles
    display("Combined Styles:")
    display("\033[1;31mBold Red Text\033[0m")
    display("\033[1;4;32mBold Underlined Green Text\033[0m")
    display("\033[1;33;44mBold Yellow on Blue\033[0m")
    display("\033[1;37;41mBold White on Red\033[0m")
    display("")
    
    # Extended colors
    display("Extended Colors:")
    display("\033[38;5;9mRed (256 color)\033[0m \033[38;5;10mGreen (256 color)\033[0m")
    display("\033[38;5;12mBlue (256 color)\033[0m")
    display("")
    
    # Get user input
    display("Now let's get some input...")
    name2 = user_type_in("What's your name? ")
    if name2:
        display(f"\033[1;32mHello, {name2}!\033[0m")
    
    age = user_write("How old are you? ")
    if age:
        display(f"\033[1;36mYou are {age} years old.\033[0m")
    
    display("Rerun test?")
    if user_type_in("type yes to rerun   ") == "yes":
        main()
    else:
        display("Goodbye!")
        exit_gui()

if __name__ == "__main__":
    run(main)  # GUI runs on main thread, your logic runs in worker thread

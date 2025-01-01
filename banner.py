from colorama import Fore

def display_banner():
    width = 64
    top_bottom = f"{Fore.GREEN}" + "#" * width
    # Define a custom ANSI escape sequence for orange
    orange = "\033[38;5;208m"
    
    # Plain texts
    left = "CryptoTaxPL - Copyright (c) 2025 by "
    name = "Przemek Malirz"
    title_plain = left + name
    contact_text = "Contact: p.malirz@gmail.com"
    
    # Center the plain title within the frame (accounting for 4 extra characters: '# ' and ' #')
    centered_title = title_plain.center(width - 4)
    # Replace the name with its orange-colored version in the centered text
    colored_centered_title = centered_title.replace(name, f"{orange}{name}{Fore.LIGHTYELLOW_EX}")
    
    line_title = f"{Fore.GREEN}# " + f"{Fore.LIGHTYELLOW_EX}" + colored_centered_title + f" {Fore.GREEN}#"
    line_contact = f"{Fore.GREEN}# " + f"{Fore.LIGHTYELLOW_EX}" + contact_text.center(width - 4) + f" {Fore.GREEN}#"
    banner = f"""
{top_bottom}
{line_title}
{line_contact}
{top_bottom}
    """
    print(banner)
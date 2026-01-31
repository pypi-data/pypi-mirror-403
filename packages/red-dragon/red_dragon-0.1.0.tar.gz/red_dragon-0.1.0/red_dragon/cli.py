#!/usr/bin/env python3
"""CLI module for Red Dragon package"""

import os
import xml.etree.ElementTree as ET

def main():
    """Main function that displays the red dragon"""
    print("")
    print("=" * 60)
    print("           RED DRAGON AWAKENS")
    print("=" * 60)
    print("")
    
    # SVG dosyasını oku ve göster
    display_dragon()
    
    print("")
    print("=" * 60)
    print("              The dragon has risen!")
    print("=" * 60)
    print("")

def display_dragon():
    """Read and display the dragon SVG"""
    # Paketin kurulu olduğu dizini bul
    package_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(os.path.dirname(package_dir), "reddragon-svg.svg")
    
    # Eğer paket kuruluysa ve SVG dosyası varsa
    if os.path.exists(svg_path):
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # SVG icerigini goster (basitlestirilmis)
            print("    RED DRAGON ASCII ART")
            print("")
            
            # SVG'den basit bir ASCII temsil oluştur
            print("""
                        /\_/\
                       ( o.o )
                        > ^ <
                       /|   |\
                      (_|   |_)
                     
              🔥 THE RED DRAGON AWAKENS 🔥
            """)
            
        except Exception as e:
            print(f"SVG dosyasi okunurken hata: {e}")
            print_dragon_fallback()
    else:
        print_dragon_fallback()

def print_dragon_fallback():
    """Fallback dragon art if SVG is not available"""
    dragon_art = r"""
                            /\_/\
                           ( o.o )
                            > ^ <
                           /|   |\
                          (_|   |_)
                         
                  THE RED DRAGON AWAKENS
    """
    print(dragon_art)

if __name__ == "__main__":
    main()

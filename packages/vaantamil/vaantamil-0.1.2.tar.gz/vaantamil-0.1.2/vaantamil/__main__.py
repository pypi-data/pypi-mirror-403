#__main__.py
import sys
from vaantamil.meimmayakkam import மெய்ம்மயக்கம்_சோதனை

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m vaantamil <TamilWord>")
        sys.exit(1)

    word = sys.argv[1]
    result = மெய்ம்மயக்கம்_சோதனை(word)
    print(result)

if __name__ == "__main__":
    main()

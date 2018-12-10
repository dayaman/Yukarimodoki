import convvoice
import yukari

def main():
    while True:
        text = convvoice.to_text()
        if text == "":
            continue
        try:
            yukari.knockApi(text, "sumire")
        except:
            pass

if __name__ == "__main__":
    main()
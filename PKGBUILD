# Maintainer: KlapkiSzatana
pkgname=budget-app
pkgver=3.1
pkgrel=1
pkgdesc="Zarządzanie Budżetem Domowym"
arch=('any')
url="https://github.com/KlapkiSzatana/budget-app"
license=('GPL-3.0')
depends=('python' 'pyside6' 'python-matplotlib' 'python-pypdf' 'python-pillow')

# Definiujemy pliki źródłowe, które będą w repozytorium
source=("budget-app.py"
        "config.py"
        "database.py"
        "dialogs.py"
        "reports.py"
        "settings_dialog.py"
        "shopping.py"
        "budget.png"
        "budget_sync.py")

# Sumy kontrolne wygenerujesz potem komendą updpkgsums
sha256sums=('a19f11269e2bd0c8020d47be691cc81ac4c0b68fbf7a6ae8d802423343f88d56'
            '92b74fdf40a4fe8dacc675eaf9e80409aa4a6a8ff7ae1d727210c2305ec483d4'
            '82fd42007d03990c3fbc328a167498d46ff5bf202c02099627c4cc5faf78d243'
            'f1700435f37a1986ac792fd370b4c4d65fa501a9fb618b34bb3b734a208adc94'
            'b672692d70a0fead5414ae80cef3691c53b71aabdea351d771f88d6f7284b199'
            '580f58395c51037d1d6735ca9da78e3ce5cfbfc2c1a0f74af6220fbcf839c2df'
            '172bcc003e78d5bfe7a9aeffceedbaee50a1acf0332373b64017591e9067084d'
            'f8e73616b675620be4c8d93d1c942502fd6932ca9c01ebf6ffe7051fc61c32f6'
            '0c1053c87a8e06f0859d4be59830ecedf33f98426f5cb93fed3c27d6fcbd268c')

package() {
    # 1. Katalog główny aplikacji
    install -d "${pkgdir}/usr/share/${pkgname}"

    # 2. Instalacja wszystkich plików .py
    # Używamy ${srcdir}, bo tam makepkg wypakowuje źródła
    install -m644 "${srcdir}"/*.py "${pkgdir}/usr/share/${pkgname}/"

    # 3. Ikona
    install -Dm644 "${srcdir}/budget.png" "${pkgdir}/usr/share/pixmaps/${pkgname}.png"

    # 4. Skrypt startowy (Wrapper)
    install -d "${pkgdir}/usr/bin"
    cat <<EOF > "${pkgdir}/usr/bin/${pkgname}"
#!/bin/sh
# Przejście do katalogu jest KLUCZOWE, by importy w Pythonie (np. import config) działały
cd /usr/share/${pkgname}
exec /usr/bin/python budget-app.py "\$@"
EOF
    chmod 755 "${pkgdir}/usr/bin/${pkgname}"

    # 5. Plik .desktop
    install -Dm644 /dev/stdin "${pkgdir}/usr/share/applications/${pkgname}.desktop" <<EOF
[Desktop Entry]
Name=Home Budget
Name[pl]=Budżet Domowy
Comment=Home Budget Management
Comment[pl]=Zarządzanie Budżetem Domowym
Exec=${pkgname}
Icon=${pkgname}
Terminal=false
Type=Application
Categories=Office;Finance;
StartupWMClass=budget-app
StartupNotify=false
EOF
}

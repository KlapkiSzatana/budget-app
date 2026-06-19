# Maintainer: KlapkiSzatana
pkgname=budget-app
pkgver=3.0
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
sha256sums=('972db462a49998e8c98974eafc2ce6657ca7446cf76bf889c64b47875422766e'
            'dfb7873a120778c7d19ff40de60c0b7d7a42a1e25cc1a1649388537e2e6dddd6'
            'dcdb6ed31ce98617f7d9d81db35f440d41c2055bf2eb6bed49a4323444b61913'
            'f1700435f37a1986ac792fd370b4c4d65fa501a9fb618b34bb3b734a208adc94'
            'b672692d70a0fead5414ae80cef3691c53b71aabdea351d771f88d6f7284b199'
            '580f58395c51037d1d6735ca9da78e3ce5cfbfc2c1a0f74af6220fbcf839c2df'
            'f26474195d30549c5207f294ef71e4cf03c0dc042ba2d486ff2413e708a01e4c'
            'f8e73616b675620be4c8d93d1c942502fd6932ca9c01ebf6ffe7051fc61c32f6'
            '8678d7286b92cf967e1b78588d6b33d54e8e02d9200b676ff715d26254bfe691')

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

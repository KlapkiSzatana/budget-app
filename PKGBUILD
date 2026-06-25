# Maintainer: KlapkiSzatana
pkgname=budget-app
pkgver=3.3
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
sha256sums=('25212ca84951f530fc134c9a50dc28647ca6076db8f7eeee9e2dcd3568004758'
            '1692de55c4e45b5120c248a4613da01df481ac6074164b07af1047736f8ce8c9'
            '76af7e71b52305a90a383bbbe595050dd932cefb8b8ea9a3711f4cf81ced7e0b'
            'f1700435f37a1986ac792fd370b4c4d65fa501a9fb618b34bb3b734a208adc94'
            'b672692d70a0fead5414ae80cef3691c53b71aabdea351d771f88d6f7284b199'
            'a98d76406100021b403dd096eaea861ea1315c623353d7f0a50528a118b83210'
            '172bcc003e78d5bfe7a9aeffceedbaee50a1acf0332373b64017591e9067084d'
            'f8e73616b675620be4c8d93d1c942502fd6932ca9c01ebf6ffe7051fc61c32f6'
            '7c90919135965e23f141b9334362ef6ab2f797c9ea5ed97059d36fe6d2afe603')

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

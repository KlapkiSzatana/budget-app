# Maintainer: KlapkiSzatana
pkgname=budget-app
pkgver=2.0.0
pkgrel=1
pkgdesc="Zarządzanie Budżetem Domowym"
arch=('any')
url="https://github.com/KlapkiSzatana/budget-app"
license=('GPL-3.0')
depends=('python' 'pyside6' 'python-matplotlib' 'python-pypdf' 'python-pillow')

# Definiujemy pliki źródłowe, które będą w repozytorium
source=("budget_app.py"
        "config.py"
        "database.py"
        "dialogs.py"
        "reports.py"
        "settings_dialog.py"
        "shopping.py"
        "budget.png"
        "forecaster.py"
        "simulator.py")

# Sumy kontrolne wygenerujesz potem komendą updpkgsums
sha256sums=('3e0a2d2663ed6351993ca66350132e147498a295449a2a20528e0d665696398b'
            'd8d7168291773bd06e331c30beb0c7db31310c890d190dc57a1b2d4b5ca3ba96'
            'e76c0a0c3260930af520a6764cd148c6dc05330cb73de0d05f7198324a076e5d'
            '335d61f7ac53e6a874109f068b74e6c35febcd62303e6b557a0de63c4e04fd75'
            'b672692d70a0fead5414ae80cef3691c53b71aabdea351d771f88d6f7284b199'
            'c13891a37d50dc650e7a920aaf0239454ca324c4d5ae878c0868f0b038023b08'
            '923604e3e10c602c6d949b908fe5e2c07064e6673c38c1e3e9c0255dbb819445'
            'f8e73616b675620be4c8d93d1c942502fd6932ca9c01ebf6ffe7051fc61c32f6'
            '97fbab80fd40b8cf81f09b97b0d55e8c22c30525df775413130cd0d4e7f88bd7'
            'feaa2e2ee977132d1c66be4d06910d8d9be419ba9a5445f6a531fb63434bfcf7')

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

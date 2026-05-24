# Maintainer: KlapkiSzatana
pkgname=budget-app
pkgver=2.1.1
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
        "forecaster.py"
        "simulator.py")

# Sumy kontrolne wygenerujesz potem komendą updpkgsums
sha256sums=('2a9ce2e55a245b33bdb1104725f6b69e59cd0277bf5f521986e0c18ebf8000be'
            'b1d2970ebd9408a84b628d1729fd097bbd86ac88e9b81004db68a242cff58c25'
            '6a1e8f8094b25c591f0898d246fd90750a407bf0e2c3927ccf80e67f77907491'
            '919c3ab66e5d5d1f8aeb65cf975389a477f4d19a83905b89d7a2a06d632d275d'
            'b672692d70a0fead5414ae80cef3691c53b71aabdea351d771f88d6f7284b199'
            'ba972600b06d369baea487e8cb20020293748871fa4ec4ca3c1c043c5fd5d3f8'
            '923604e3e10c602c6d949b908fe5e2c07064e6673c38c1e3e9c0255dbb819445'
            'f8e73616b675620be4c8d93d1c942502fd6932ca9c01ebf6ffe7051fc61c32f6'
            '907ca460f882f85e83937f026390bfe6c4664846fa42b9d9c076930108b93d2f'
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

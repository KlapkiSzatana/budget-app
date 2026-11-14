# Maintainer: KlapkiSzatana
pkgname=budget-app
pkgver=1.4.1
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
sha256sums=('00539a84cef049c1d3cb5c403514f849979146eed46fa2c1a8e939ada2cb1453'
            'aacdd332faaea2c893f51ee9183c477a20a8583dc899b542a924fc4447f66407'
            '56f95665746e7ee8fe4a8448935fe333fc4c6282189aa8fedc0b1cf001291bf4'
            '165c1b14bd073429445653e92eaacbebafada4b7ddb4006c0a067efa850f79ad'
            'e64e708372afba558a753b3902711b0481e5f75ab7be00040f75e3a61136b6d7'
            'a98d76406100021b403dd096eaea861ea1315c623353d7f0a50528a118b83210'
            '702219f219a303e70d4433ae7468c8a8ec8841f32d5221f4a56f2e4e309eb52c'
            'f8e73616b675620be4c8d93d1c942502fd6932ca9c01ebf6ffe7051fc61c32f6'
            '0f4a420ee6ae4f1f3e505feb6112c9d5f1a1f3c1d544682e191aa6f03c4f2855')

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
Name[pl]=Kajet
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

# Maintainer: KlapkiSzatana
pkgname=budget-app
pkgver=1.3.5
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
sha256sums=('fc8cca314f460432fa0090e4c45b3aadb16a8ea50f1f652119dc74f9f3d7a99e'
            'b55993ec56fc8d7806e7314ced6f946869b6527d9a0061aae418dfbc76cec3c0'
            'a11830c0709b67e9db6eac52b3404974e44bbdf6b21ab705b9e72c7522a5bc2e'
            'dd89fee23b13aed7557ae403d64ec6e30c8bdd6be1d024d40c171f8f24b8e51e'
            'e64e708372afba558a753b3902711b0481e5f75ab7be00040f75e3a61136b6d7'
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

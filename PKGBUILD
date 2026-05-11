# Maintainer: KlapkiSzatana
pkgname=budget-app
pkgver=1.6.2
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
        "budget.png")

# Sumy kontrolne wygenerujesz potem komendą updpkgsums
sha256sums=('0faa462dc55988c3d135cfa28534c268abd921a28b002960e56d6ed7c5e0bc22'
            '90fdbf87036f123a54e1df5c7e0e24ad94548095d9ee103133f049d888719e40'
            '1e5813156932d4267e3a6fd668507bc76f7e78ebba98ac83d7a624a4ef1cb862'
            'ee25d41379687f7a1d8fa6ccbd0165c1343142e69bdef1cfc138cc3201aa04f2'
            'defcf0391c6b5519c98cc96644d5dc847dba1334dfaab44c4547a94eb61288ce'
            '51bb7e0156d6803d095b04a9ee53a435fd0215e2a41187dbb5e63b51edfda896'
            '801ef906322352879e06b7aafcc810e9ea3919d99e52d94f1c924cc9d872b1b0'
            'f8e73616b675620be4c8d93d1c942502fd6932ca9c01ebf6ffe7051fc61c32f6')

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

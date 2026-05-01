# Maintainer: Heisenberg (KlapkiSzatana)
pkgname=budget-app
pkgver=1.3.9
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
sha256sums=('5f9d57d8a66bb1de9ee22d7d7b40e281e1dc93b4418facce6ad39da2db776934'
            'a51703351bc2fdf3b65b9180d857fbd30aa6ad3d73b14078dd64325a428d9637'
            '3d71f5fe03cd683efd9afbab2ddcbb2200baeba6ab57a4724e71e40bc838f3ae'
            'd3a997960201b0b626713f41d0b6c8225a34760cffcf8b5bece7e6437bb826e6'
            '3145d4a2aa00e7858044fdefccd116a4cb8e0663054a44264480ae7a9bd24c27'
            '51bb7e0156d6803d095b04a9ee53a435fd0215e2a41187dbb5e63b51edfda896'
            'c8cac3a60f30584267765a0549e9cc9665719ae7151f8cfe459bb2cc63f6964c'
            '7919b3aefeb2529d429408fd618a560ea6456e5a163b9bd6afeab4397d6b311a')

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
EOF
}

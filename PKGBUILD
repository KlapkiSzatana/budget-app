# Maintainer: KlapkiSzatana
pkgname=budget-app
pkgver=1.6.0
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
sha256sums=('23de18ff29c277a889a106211f5f067930c9598d838cb06786fb01d8efdd2815'
            'fdd635c82c62d89165ca736b77085771fae70f364c6dcdb2577e9b958f963d9e'
            '1e5813156932d4267e3a6fd668507bc76f7e78ebba98ac83d7a624a4ef1cb862'
            'a035199b868a60a64e94df62a838f9a2e03e9b72514f56bae17cce59805a8b94'
            'defcf0391c6b5519c98cc96644d5dc847dba1334dfaab44c4547a94eb61288ce'
            '51bb7e0156d6803d095b04a9ee53a435fd0215e2a41187dbb5e63b51edfda896'
            'c8cac3a60f30584267765a0549e9cc9665719ae7151f8cfe459bb2cc63f6964c'
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

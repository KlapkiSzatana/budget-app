# Maintainer: KlapkiSzatana
pkgname=budget-app
pkgver=1.5.1
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
sha256sums=('2c0fae20fe2851b2787089ccb6256105ea3acc6b9a7438b49184c21900e405fb'
            '46e63ae30718a411f002e8c45841b0aa2714f0e177a85c3f5acad05a46188bab'
            '1e5813156932d4267e3a6fd668507bc76f7e78ebba98ac83d7a624a4ef1cb862'
            'a035199b868a60a64e94df62a838f9a2e03e9b72514f56bae17cce59805a8b94'
            'defcf0391c6b5519c98cc96644d5dc847dba1334dfaab44c4547a94eb61288ce'
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

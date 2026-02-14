# Maintainer: KlapkiSzatana
pkgname=budget-app
pkgver=0.9.6
pkgrel=1
pkgdesc="Zarządzanie Budżetem Domowym"
arch=('any')
url="https://github.com/KlapkiSzatana/budget-app"
license=('GPL-3.0')

depends=('python' 'pyside6' 'python-matplotlib')
makedepends=('git')

source=("${url}/archive/refs/tags/v${pkgver}.tar.gz")


sha256sums=('SKIP')

package() {

    cd "budget-app-${pkgver}"

    # 1. Tworzymy folder docelowy w systemie
    install -d "${pkgdir}/usr/share/${pkgname}"

    # 2. Kopiujemy WSZYSTKIE pliki .py (główny + moduły: charts, database, config itp.)
    install -m644 *.py "${pkgdir}/usr/share/${pkgname}/"

    # Opcjonalnie: Usuwamy skrypty budowania, bo w paczce systemowej są zbędne
    rm -f "${pkgdir}/usr/share/${pkgname}/build.sh"
    rm -f "${pkgdir}/usr/share/${pkgname}/compile.sh"

    # 3. Instalujemy tłumaczenia (folder locales)
    # cp -r zachowuje strukturę katalogów
    cp -r locales "${pkgdir}/usr/share/${pkgname}/"
    # Naprawiamy uprawnienia dla folderów i plików tłumaczeń (dla bezpieczeństwa)
    find "${pkgdir}/usr/share/${pkgname}/locales" -type d -exec chmod 755 {} +
    find "${pkgdir}/usr/share/${pkgname}/locales" -type f -exec chmod 644 {} +

    # 4. Instalacja ikonki (zmieniamy nazwę na nazwę paczki dla porządku)
    install -d "${pkgdir}/usr/share/pixmaps"
    install -m644 budget.png "${pkgdir}/usr/share/pixmaps/${pkgname}.png"

    # 5. Tworzymy skrypt startowy (Wrapper) w /usr/bin
    install -d "${pkgdir}/usr/bin"
    cat <<EOF > "${pkgdir}/usr/bin/${pkgname}"
#!/bin/sh
# Wchodzimy do katalogu, żeby Python widział pliki config.py, database.py obok siebie
cd /usr/share/${pkgname}
export APP_ID="${pkgname}"
# Uruchamiamy plik główny (budget-app.py)
exec /usr/bin/python budget-app.py "\$@"
EOF
    chmod 755 "${pkgdir}/usr/bin/${pkgname}"

    # 6. Generujemy plik .desktop (żeby było w menu Start)
    install -d "${pkgdir}/usr/share/applications"
    cat <<EOF > "${pkgdir}/usr/share/applications/${pkgname}.desktop"
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

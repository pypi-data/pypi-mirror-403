from PySide6.QtGui import QCloseEvent, Qt
from PySide6.QtWidgets import QVBoxLayout, QLabel, QWidget
from typing_extensions import override

from clochette.presentation.widget.QTitle import QTitle


class QAboutClochette(QWidget):
    _dependencies = {
        "icalendar": {
            "url": "https://icalendar.readthedocs.io/",
            "license": "BSD",
            "license_url": "https://github.com/collective/icalendar/blob/master/LICENSE.rst",
        },
        "python-dateutil": {
            "url": "https://dateutil.readthedocs.io/",
            "license": "BSD 3-Clause",
            "license_url": "https://github.com/dateutil/dateutil/blob/master/LICENSE",
        },
        "requests": {
            "url": "https://requests.readthedocs.io/",
            "license": "Apache 2.0",
            "license_url": "https://github.com/psf/requests/blob/master/LICENSE",
        },
        "PySide6": {"url": "https://www.qt.io/", "license": "LGPL", "license_url": "https://www.qt.io/licensing/"},
        "reactivex": {
            "url": "https://rxpy.readthedocs.io/",
            "license": "MIT",
            "license_url": "https://github.com/ReactiveX/RxPY/blob/master/LICENSE",
        },
        "platformdirs": {
            "url": "https://platformdirs.readthedocs.io/",
            "license": "MIT",
            "license_url": "https://github.com/platformdirs/platformdirs/blob/master/LICENSE",
        },
        "isodate": {
            "url": "https://github.com/gweis/isodate/",
            "license": "BSD 3-Clause",
            "license_url": "https://github.com/gweis/isodate/blob/master/LICENSE",
        },
        "humanize": {
            "url": "https://github.com/python-humanize/humanize",
            "license": "MIT",
            "license_url": "https://github.com/python-humanize/humanize/blob/main/LICENSE",
        },
        "babel": {
            "url": "https://babel.pocoo.org/",
            "license": "BSD 3-Clause",
            "license_url": "https://github.com/python-babel/babel/blob/master/LICENSE",
        },
        "keyring": {
            "url": "https://github.com/jaraco/keyring",
            "license": "MIT",
            "license_url": "https://pypi.org/project/keyring/",
        },
        "peewee": {
            "url": "https://github.com/coleifer/peewee",
            "license": "BSD 3-Clause",
            "license_url": "https://raw.githubusercontent.com/coleifer/peewee/refs/heads/master/LICENSE",
        },
        "Lucide": {
            "url": "https://lucide.dev/",
            "license": "ISC",
            "license_url": "https://lucide.dev/license",
        },
    }

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # About Section
        about_title = QTitle(self.tr("About Clochette"))
        layout.addWidget(about_title)

        program_description = self.tr("Clochette (from the French word meaning little bell) is a desktop reminder application written in Python and QT.")
        description_label = QLabel(program_description)
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        program_license = self.tr(
            'This project is licensed under the <a href="https://gitlab.com/sketyl/clochette/-/blob/main/LICENSE">MIT License</a>. '
            'Project: <a href="https://gitlab.com/sketyl/clochette">https://gitlab.com/sketyl/clochette</a>'
        )
        license_label = QLabel(program_license)
        license_label.setWordWrap(True)
        license_label.setOpenExternalLinks(True)
        layout.addWidget(license_label)

        # Dependencies Section
        dependencies_label = QTitle(self.tr("Dependencies"))
        layout.addWidget(dependencies_label)

        for name, info in self._dependencies.items():
            project_url = info["url"]
            license_type = info["license"]
            license_url = info["license_url"]
            label_text = (
                f'<b>{name}</b> (<a href="{license_url}">{license_type}</a>): <a href="{project_url}">{project_url}</a>'
            )
            label = QLabel(label_text)
            label.setOpenExternalLinks(True)
            layout.addWidget(label)

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()

import os
import shutil

import flet as ft

# Nama folder tujuan -> (ekstensi, ikon, warna)
KATEGORI = {
    "Gambar": ([".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"], ft.Icons.IMAGE_OUTLINED, "#4C8DF6"),
    "Dokumen": ([".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"], ft.Icons.DESCRIPTION_OUTLINED, "#F2A93B"),
    "Video": ([".mp4", ".mkv", ".avi", ".mov", ".3gp"], ft.Icons.VIDEOCAM_OUTLINED, "#E2587A"),
    "Audio": ([".mp3", ".wav", ".m4a", ".ogg", ".flac"], ft.Icons.MUSIC_NOTE_OUTLINED, "#8E6FE0"),
    "Arsip": ([".zip", ".rar", ".7z", ".tar", ".gz"], ft.Icons.FOLDER_ZIP_OUTLINED, "#9C8B76"),
    "Aplikasi": ([".apk"], ft.Icons.ANDROID, "#35B27E"),
    "Kode": ([".py", ".js", ".html", ".css", ".json"], ft.Icons.CODE, "#1F9CB0"),
    "Lainnya": ([], ft.Icons.INSERT_DRIVE_FILE_OUTLINED, "#8D9A94"),
}

FOLDER_AWAL = "/storage/emulated/0/Download"

EKSTENSI = {ext: nama for nama, (daftar, _, _) in KATEGORI.items() for ext in daftar}


def kategori_dari(nama_file: str) -> str:
    ext = os.path.splitext(nama_file)[1].lower()
    return EKSTENSI.get(ext, "Lainnya")


def path_unik(path: str) -> str:
    """Tambahkan (1), (2), dst. jika nama file sudah ada di tujuan."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    n = 1
    while os.path.exists(f"{base} ({n}){ext}"):
        n += 1
    return f"{base} ({n}){ext}"


def pindai(folder: str) -> dict:
    """Kembalikan {kategori: [nama file]} untuk file di level teratas folder."""
    hasil = {}
    for entri in os.scandir(folder):
        if not entri.is_file() or entri.name.startswith("."):
            continue
        hasil.setdefault(kategori_dari(entri.name), []).append(entri.name)
    return hasil


def contoh_nama(files: list) -> str:
    teks = ", ".join(sorted(files)[:2])
    sisa = len(files) - 2
    return f"{teks}  +{sisa}" if sisa > 0 else teks


def main(page: ft.Page):
    page.title = "Rapikan File"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.theme = ft.Theme(color_scheme_seed="#2F6F5E")
    page.dark_theme = ft.Theme(color_scheme_seed="#2F6F5E")

    state = {"rencana": {}, "riwayat": []}

    def info(teks: str):
        page.open(ft.SnackBar(ft.Text(teks)))

    # ---------- Komponen ----------
    app_label = ft.Text("Rapikan File", size=13, color=ft.Colors.ON_SURFACE_VARIANT)
    judul = ft.Text(size=30, weight=ft.FontWeight.W_700, height=1.15)
    sub = ft.Text(size=14, color=ft.Colors.ON_SURFACE_VARIANT)

    kolom_folder = ft.TextField(
        value=FOLDER_AWAL,
        border=ft.InputBorder.NONE,
        text_size=14,
        dense=True,
        content_padding=ft.padding.symmetric(horizontal=0, vertical=8),
        expand=True,
    )

    bar = ft.Row(spacing=3, height=18)
    daftar = ft.Column(spacing=0)

    tombol_rapikan = ft.FilledButton(
        "Rapikan",
        icon=ft.Icons.DRIVE_FILE_MOVE_OUTLINE,
        height=56,
        expand=True,
        disabled=True,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=18),
            bgcolor={
                ft.ControlState.DEFAULT: ft.Colors.ON_SURFACE,
                ft.ControlState.DISABLED: ft.Colors.SURFACE_CONTAINER_HIGHEST,
            },
            color={
                ft.ControlState.DEFAULT: ft.Colors.SURFACE,
                ft.ControlState.DISABLED: ft.Colors.ON_SURFACE_VARIANT,
            },
        ),
    )
    tombol_urungkan = ft.TextButton("Urungkan", visible=False)

    # ---------- Logika ----------
    def gambar_bar(rencana: dict):
        bar.controls.clear()
        if not rencana:
            bar.controls.append(
                ft.Container(
                    expand=1,
                    border_radius=9,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                )
            )
            return
        for nama, files in rencana.items():
            bar.controls.append(
                ft.Container(
                    expand=len(files),
                    border_radius=9,
                    bgcolor=KATEGORI[nama][2],
                    tooltip=f"{nama}: {len(files)}",
                )
            )

    def segarkan(_=None):
        folder = kolom_folder.value.strip()
        daftar.controls.clear()
        state["rencana"] = {}
        error = None

        if not os.path.isdir(folder):
            error = "Folder tidak ditemukan atau belum diberi izin akses."
        else:
            try:
                state["rencana"] = pindai(folder)
            except PermissionError:
                error = "Akses ditolak. Aktifkan izin “Akses semua file” di pengaturan aplikasi."

        rencana = {n: state["rencana"][n] for n in KATEGORI if n in state["rencana"]}
        state["rencana"] = rencana
        total = sum(len(v) for v in rencana.values())

        # Teks utama berubah sesuai keadaan
        if error:
            judul.value = "Folder tidak bisa dibuka"
            sub.value = error
        elif total == 0:
            judul.value = "Folder ini sudah rapi"
            sub.value = (
                f"{len(state['riwayat'])} file baru saja dipindahkan."
                if state["riwayat"]
                else "Tidak ada file lepas yang perlu dipindahkan."
            )
        else:
            nama_folder = os.path.basename(folder.rstrip("/\\")) or folder
            judul.value = f"{total} file belum tertata"
            sub.value = f"Di folder {nama_folder}, terbagi dalam {len(rencana)} jenis."

        gambar_bar(rencana)

        for nama, files in rencana.items():
            _, ikon, warna = KATEGORI[nama]
            daftar.controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=10),
                    content=ft.Row(
                        [
                            ft.Container(
                                width=40,
                                height=40,
                                border_radius=12,
                                bgcolor=ft.Colors.with_opacity(0.14, warna),
                                alignment=ft.alignment.center,
                                content=ft.Icon(ikon, size=20, color=warna),
                            ),
                            ft.Column(
                                [
                                    ft.Text(nama, size=15, weight=ft.FontWeight.W_500),
                                    ft.Text(
                                        contoh_nama(files),
                                        size=12,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                            ft.Text(
                                str(len(files)),
                                size=18,
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        spacing=14,
                    ),
                )
            )

        tombol_rapikan.disabled = total == 0
        tombol_rapikan.text = f"Rapikan {total} file" if total else "Rapikan"
        page.update()

    def rapikan(_):
        folder = kolom_folder.value.strip()
        riwayat = []
        gagal = 0

        for nama_kat, files in state["rencana"].items():
            tujuan = os.path.join(folder, nama_kat)
            for nama in files:
                asal = os.path.join(folder, nama)
                try:
                    os.makedirs(tujuan, exist_ok=True)
                    baru = path_unik(os.path.join(tujuan, nama))
                    shutil.move(asal, baru)
                    riwayat.append((asal, baru))
                except OSError:
                    gagal += 1

        state["riwayat"] = riwayat
        tombol_urungkan.visible = bool(riwayat)
        segarkan()

        pesan = f"{len(riwayat)} file dipindahkan"
        if gagal:
            pesan += f", {gagal} gagal"
        info(pesan)

    def urungkan(_):
        kembali = 0
        for asal, baru in reversed(state["riwayat"]):
            try:
                shutil.move(baru, path_unik(asal))
                kembali += 1
            except OSError:
                pass

        folder = kolom_folder.value.strip()
        for nama_kat in KATEGORI:
            p = os.path.join(folder, nama_kat)
            try:
                if os.path.isdir(p) and not os.listdir(p):
                    os.rmdir(p)
            except OSError:
                pass

        state["riwayat"] = []
        tombol_urungkan.visible = False
        segarkan()
        info(f"{kembali} file dikembalikan")

    def hasil_pilih(e: ft.FilePickerResultEvent):
        if e.path:
            kolom_folder.value = e.path
            state["riwayat"] = []
            tombol_urungkan.visible = False
            segarkan()

    picker = ft.FilePicker(on_result=hasil_pilih)
    page.overlay.append(picker)

    tombol_rapikan.on_click = rapikan
    tombol_urungkan.on_click = urungkan
    kolom_folder.on_submit = segarkan
    kolom_folder.on_blur = segarkan

    # ---------- Tampilan ----------
    pemilih_folder = ft.Container(
        padding=ft.padding.only(left=16, right=6),
        border_radius=16,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        content=ft.Row(
            [
                ft.Icon(ft.Icons.FOLDER_OUTLINED, size=20, color=ft.Colors.ON_SURFACE_VARIANT),
                kolom_folder,
                ft.TextButton("Pilih", on_click=lambda _: picker.get_directory_path()),
            ],
            spacing=10,
        ),
    )

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Container(
                expand=True,
                padding=ft.padding.only(left=24, right=24, top=24, bottom=20),
                content=ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        app_label,
                        ft.Container(height=14),
                        judul,
                        ft.Container(height=6),
                        sub,
                        ft.Container(height=22),
                        bar,
                        ft.Container(height=14),
                        ft.Column([daftar], expand=True, scroll=ft.ScrollMode.AUTO),
                        pemilih_folder,
                        ft.Container(height=12),
                        ft.Row([tombol_rapikan]),
                        ft.Row([tombol_urungkan], alignment=ft.MainAxisAlignment.CENTER),
                    ],
                ),
            ),
        )
    )

    segarkan()


ft.app(target=main)
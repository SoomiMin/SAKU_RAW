# 💖 Editado por Rami
# SAKU_RAW — Bot de Discord que revisa sitios de raws
# Detecta automáticamente qué evento A–J aplicar según estructura
# Ignora eternal, lectorjpg, catharsis y drive
# Devuelve solo el último capítulo (sin fecha)

import os
import re
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands

# --- Variables de entorno ---
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_IDS = [int(x.strip()) for x in os.getenv("GUILD_IDS", "").split(",") if x.strip()]

# --- Configuración del bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ============================================================
# 🧩 EVENTOS A–J (adaptados sin Selenium)
# ============================================================

def evento_a(soup):
    contenedores = soup.select('astro-slot > div[data-hk]')
    if contenedores:
        ultimo_div = contenedores[-1]
        enlace = ultimo_div.select_one('a.link-hover')
        if enlace:
            return enlace.get_text(strip=True)
    return None

def evento_b(soup):
    b_tag = soup.select_one("div.main b")
    return b_tag.get_text(strip=True) if b_tag else None

def evento_c(soup):
    for li in soup.select('li.flex.justify-between'):
        spans = li.find_all('span')
        if len(spans) == 2:
            return spans[0].get_text(strip=True)
    return None

def evento_d(soup):
    contenedor = soup.select_one('div.all_data_list ul.fed-part-rows li a')
    return contenedor.get_text(strip=True) if contenedor else None

def evento_e(html):
    match = re.search(r'<span class="epcur epcurlast">\s*(.*?)\s*</span>', html, re.IGNORECASE)
    return match.group(1).strip() if match else None

def evento_f(soup):
    spans = soup.select('div.title-item span.text')
    texto_libres = [s.get_text(strip=True) for s in spans if "text-locked" not in s.get("class", [])]
    return texto_libres[-1] if texto_libres else None

def evento_g(soup):
    primer_li = soup.select_one("li.wp-manga-chapter a")
    if primer_li:
        texto = primer_li.get_text(strip=True)
        return texto if "Chapter" in texto else None
    return None

def evento_h(html):
    match = re.search(r'title="(Ch\.\s*\d+)"', html)
    return match.group(1) if match else None

def evento_i(html):
    match = re.search(r'<div class="latest-chapters">.*?<a[^>]*>\s*<strong[^>]*>(.*?)</strong>', html, re.DOTALL)
    return match.group(1).strip() if match else None

def evento_j(soup):
    bloques = soup.select('div.group.flex.flex-col')
    for bloque in bloques:
        sub = bloque.select_one('div.space-x-1 a.link-hover')
        if sub:
            texto = sub.get_text(strip=True)
            span = bloque.select_one('div.space-x-1 span.opacity-80')
            extra = span.get_text(strip=True) if span else ""
            return f"{texto} {extra}".strip()
    return None

# ============================================================
# 🔍 FUNCIÓN GENERAL DE DETECCIÓN AUTOMÁTICA
# ============================================================

def detectar_evento(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None, "Error HTTP"

        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        for letra, func in [
            ("A", lambda: evento_a(soup)),
            ("B", lambda: evento_b(soup)),
            ("C", lambda: evento_c(soup)),
            ("D", lambda: evento_d(soup)),
            ("E", lambda: evento_e(html)),
            ("F", lambda: evento_f(soup)),
            ("G", lambda: evento_g(soup)),
            ("H", lambda: evento_h(html)),
            ("I", lambda: evento_i(html)),
            ("J", lambda: evento_j(soup)),
        ]:
            resultado = func()
            if resultado:
                return resultado, letra

        return None, "No detectado"

    except Exception as e:
        return None, str(e)

# ============================================================
# 🚀 COMANDO !raw
# ============================================================

@bot.event
async def on_ready():
    print(f"✨ Saku_RAW está en línea como {bot.user}")

@bot.command()
async def raw(ctx):
    if ctx.guild.id not in GUILD_IDS:
        return await ctx.send("❌ Este comando no está autorizado en este servidor.")

    await ctx.send("🔍 Buscando enlaces de RAW en los mensajes fijados...")
    pinned = await ctx.channel.pins()

    encontrados = False

    for msg in pinned:
        urls = re.findall(r"https?://[^\s>]+", msg.content)
        for url in urls:
            if any(x in url for x in [
                "eternalmangas.org", "lectorjpg.com", "catharsisworld.dig-it.info", "drive.google.com"
            ]):
                continue

            encontrados = True

            lineas = msg.content.splitlines()
            texto_arriba = ""
            for i, linea in enumerate(lineas):
                if url in linea and i > 0:
                    posible_texto = lineas[i - 1].strip()
                    if posible_texto:
                        texto_arriba = posible_texto
                    break

            dominio = re.search(r"https?://(?:www\.)?([^/]+)/", url)
            sitio = dominio.group(1) if dominio else "Sitio desconocido"

            titulo_embed = f"{texto_arriba} ({sitio.upper()})" if texto_arriba else f"{sitio.upper()}"

            cap, evento = detectar_evento(url)

            if cap:
                embed = discord.Embed(
                    title=titulo_embed,
                    description=f"Último capítulo: {cap}",
                    color=0x6AFF7A
                )
            else:
                embed = discord.Embed(
                    title=titulo_embed,
                    description="❌ Estructura incompatible — Revisión manual requerida",
                    color=0xFF5C5C
                )

            await ctx.send(embed=embed)

    if not encontrados:
        embed = discord.Embed(
            title="🌸 Saku_RAW — *Sin enlaces válidos*",
            description="No se encontraron enlaces de raws en los mensajes fijados.\n",
            color=0xF8C8DC
        )
        embed.set_footer(text="Asegúrate de fijar mensajes con los enlaces correctos 💖")
        await ctx.send(embed=embed)

# ============================================================
# 🩷 EJECUTAR BOT
# ============================================================

bot.run(TOKEN)

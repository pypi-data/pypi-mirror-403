import pytest
from dgc_pricecharting_ingest.url import _simple_slug, pricecharting_url

BASE = "https://www.pricecharting.com/game"


@pytest.mark.parametrize(
    "console,product,expected",
    [
        (
            "Atari ST",
            "Leisure Suit Larry 1, 2 & 3",
            f"{BASE}/atari-st/leisure-suit-larry-1-2-&-3",
        ),
        (
            "Magic Warhammer 40,000",
            "Celestine, the Living Saint #10",
            f"{BASE}/magic-warhammer-40,000/celestine-the-living-saint-10",
        ),
        (
            "Magic Unstable",
            "Half-Shark, Half-",
            f"{BASE}/magic-unstable/half-shark-half-",
        ),
        (
            "Magic Unfinity",
            "How Is This a Par Three?! [Galaxy Foil]",
            f"{BASE}/magic-unfinity/how-is-this-a-par-three-galaxy-foil",
        ),
        (
            "Magic Unhinged",
            "Framed! [Foil]",
            f"{BASE}/magic-unhinged/framed-foil",
        ),
        (
            "Amiga",
            "Monkey Island 2: LeChuck’s Revenge",
            f"{BASE}/amiga/monkey-island-2-lechuck’s-revenge",
        ),
        (
            "Pokemon Japanese Promo",
            "Umbreon [Daisuki Club 7,200 Pts.] #54/L-P",
            f"{BASE}/pokemon-japanese-promo/umbreon-daisuki-club-7,200-pts-54l-p",
        ),
        (
            "Pokemon Japanese Promo",
            "PokePark‘s Celebi #44/PCG-P",
            f"{BASE}/pokemon-japanese-promo/pokepark‘s-celebi-44pcg-p",
        ),
        (
            "Pokemon Japanese Gaia Volcano",
            "Nidoran♀ #25",
            f"{BASE}/pokemon-japanese-gaia-volcano/nidoran♀-25",
        ),
        (
            "Pokemon Japanese Cruel Traitor",
            "Nidoran♂ #20",
            f"{BASE}/pokemon-japanese-cruel-traitor/nidoran♂-20",
        ),
        (
            "Magic Unstable",
            "Monkey-",
            f"{BASE}/magic-unstable/monkey-",
        ),
        (
            "Magic Unhinged",
            "_____ [Foil]",
            f"{BASE}/magic-unhinged/_____-foil",
        ),
        (
            "Magic Commander 2013",
            "Borrowing 100,000 Arrows",
            f"{BASE}/magic-commander-2013/borrowing-100,000-arrows",
        ),
        (
            "Lorcana Ursula's Return",
            "Flotsam - Ursula's \"Baby\" #43",
            f"{BASE}/lorcana-ursula's-return/flotsam-ursula's-\"baby\"-43",
        ),
        (
            "YuGiOh World Championship 2025 Limited Pack",
            "Maliss <C> GWC-06 [Emblazoned] 25LP-EN017",
            f"{BASE}/yugioh-world-championship-2025-limited-pack/maliss-<c>-gwc-06-emblazoned-25lp-en017",
        ),
        (
            "YuGiOh 2025 Mega Pack Tin",
            "S:P Little Knight MP25-EN047",
            f"{BASE}/yugioh-2025-mega-pack-tin/sp-little-knight-mp25-en047",
        ),
        (
            "YuGiOh Tactical Evolution",
            "Damage = Reptile TAEV-EN067",
            f"{BASE}/yugioh-tactical-evolution/damage-=-reptile-taev-en067",
        ),
        (
            "YuGiOh Ignition Assault",
            "Water Leviathan @Ignister IGAS-EN034",
            f"{BASE}/yugioh-ignition-assault/water-leviathan-@ignister-igas-en034",
        ),
        (
            "YuGiOH Japanese Booster Pack Collectors Tin",
            "Chaos Emperor Dragon - Envoy of the End BPT-J02",
            f"{BASE}/yugioh-japanese-booster-pack-collectors-tin/chaos-emperor-dragon-envoy-of-the-end-bpt-j02",
        ),
        (
            "Atari 2600",
            "M*A*S*H",
            f"{BASE}/atari-2600/m*a*s*h",
        ),
        (
            "Asian English Playstation Vita",
            "Hyperdimension Neptunia Re;Birth1",
            f"{BASE}/asian-english-playstation-vita/hyperdimension-neptunia-re;birth1",
        ),
        (
            "Amiga",
            "Darius+",
            f"{BASE}/amiga/darius+",
        ),
        (
            "Pokemon 2001 Topps Johto",
            "Unstoppable Team! [Foil]",
            f"{BASE}/pokemon-2001-topps-johto/unstoppable-team-foil",
        ),
        (
            "Pokemon 1999 Topps Movie",
            "Don't Cry, Togepi [Rainbow Foil] #43",
            f"{BASE}/pokemon-1999-topps-movie/don't-cry-togepi-rainbow-foil-43",
        ),
        (
            "Apple II",
            "Death Race '82",
            f"{BASE}/apple-ii/death-race-'82",
        ),
        (
            "Pokemon 1998 KFC",
            "Charizard #6",
            f"{BASE}/pokemon-1998-kfc/charizard-6",
        ),
        (
            "Pokemon 1999 Topps Movie",
            "A Call to Arms [Foil] #16",
            f"{BASE}/pokemon-1999-topps-movie/a-call-to-arms-foil-16",
        ),
        (
            "Pokemon Astral Radiance",
            "Build & Battle Display Box",
            f"{BASE}/pokemon-astral-radiance/build-&-battle-display-box",
        ),
    ],
)
def test_examples_full_url(console, product, expected):
    assert pricecharting_url(console, product) == expected


@pytest.mark.parametrize(
    "raw,expected_slug",
    [
        ("A Call to Arms [Foil] #16", "a-call-to-arms-foil-16"),
        ("Build & Battle   Display Box  ", "build-&-battle-display-box"),
        ("  Pokemon   Astral Radiance  ", "pokemon-astral-radiance"),
        ("Hello/World Edition", "helloworld-edition"),  # slash removed by current regex
        ("A - - B", "a-b"),  # multiple hyphens collapse
    ],
)
def test_simple_slug_behaviour(raw, expected_slug):
    assert _simple_slug(raw) == expected_slug


def test_slug_and_url_consistency_with_ampersand():
    console = "Pokemon Astral Radiance"
    product = "Build & Battle Display Box"
    slug = _simple_slug(product)
    assert slug == "build-&-battle-display-box"
    assert pricecharting_url(console, product).endswith("/" + slug)


def test_empty_inputs():
    # when inputs are empty, slug returns empty string and url includes empty segments
    assert _simple_slug("") == ""
    assert pricecharting_url("", "") == f"{BASE}//"


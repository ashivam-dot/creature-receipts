# Content calendar

The studio takes topics from here: anniversaries dated within the next 7 days first, then the backlog,
rotating through the series and taking each one's most-read topic (by English Wikipedia pageviews) first.
It marks a topic `— making (epNNN)` when its Short starts and `— done (epNNN)` when the Short is
scheduled. A Short that fails the quality gate is `— parked` (it comes back once after 14 days), and one
that fails again, or whose research is too thin, is `— dropped`. The daily routine adds new topics on its
own (`auto.add_topics`).

Each topic is one line naming the story, its year if it has one, and its twist, with an English Wikipedia
article behind it. Every topic still has to pass the two-source rule.

Seeded 2026-10-01, when the channel moved from animals to historical tragedies. Each line starts with the
exact title of its English Wikipedia article (checked with the API: it exists, isn't a redirect or a
disambiguation page). Only events at least 75 years old, so no living families are retold for views; no
event is told for its gore. Space topics belong to the sister channel Universe Receipts and never go here.

## Anniversaries (publish on the date, 7 p.m. Eastern)

| Date | Story | Series |
|---|---|---|
| Oct 5 | R101 (1930): Britain's giant airship crashed in France on its first overseas flight, after it was sent off on schedule with the air minister aboard — making (ep025) | Warnings Ignored |
| Oct 8 | Peshtigo fire (1871): the deadliest wildfire in American history burned the same night as the Great Chicago Fire, and was nearly forgotten because of it — making (ep026) | The Last Hours |
| Oct 8 | Great Chicago Fire (1871): Mrs. O'Leary's cow took the blame, but the reporter who spread the story later admitted he made it up — making (ep027) | The Last Hours |
| Oct 17 | London Beer Flood (1814): a vat burst at a brewery and a wave of more than a million liters of beer swept through a poor London parish | The Last Hours |
| Oct 24 | Eruption of Mount Vesuvius in 79 AD: a charcoal inscription found at Pompeii in 2018 suggests the eruption came in autumn, not on August 24 as long believed | The Last Hours |
| Oct 25 | Charge of the Light Brigade (1854): a misread order sent the light cavalry straight down a valley ringed with Russian guns | Warnings Ignored |
| Nov 1 | 1755 Lisbon earthquake: it struck on All Saints' Day, when the churches were full, and people who fled to the open waterfront were hit by a tsunami | The Last Hours |
| Nov 20 | Essex (whaleship) (1820): after a sperm whale sank the ship, the crew steered away from the nearest islands for fear of cannibals | Sole Survivors |
| Nov 25 | White Ship (1120): its sinking drowned the king of England's only legitimate son, and the fight over his throne became a civil war | Fallen Empires |
| Nov 28 | Cocoanut Grove fire (1942): hundreds died in a Boston nightclub whose main exit was a revolving door and whose other doors were locked or hidden | Warnings Ignored |

## Backlog

### The Last Hours

- Sinking of the Titanic (1912): the lookouts had no binoculars, because the key to their locker left the ship with an officer removed before the voyage
- Sinking of the RMS Lusitania (1915): the liner sank in 18 minutes, after a German warning ran next to its own sailing notice in New York newspapers
- Hindenburg disaster (1937): the airship burned in about half a minute, yet most of the people aboard survived
- 1883 eruption of Krakatoa: its final explosion was heard thousands of kilometers away, on Rodrigues island in the Indian Ocean
- 1906 San Francisco earthquake: the fires afterwards did more damage than the shaking
- Halifax Explosion (1917): a burning munitions ship blew up in the harbor, the largest man-made explosion before the atomic bomb
- MV Wilhelm Gustloff (1945): its sinking in the Baltic was the deadliest loss of a single ship in history
- SS Eastland (1915): it rolled over while still tied to its Chicago dock, and 844 people died in water about 20 feet deep
- Great Fire of London (1666): only a handful of deaths were recorded, though the true toll is unknown

### Lost Cities

- Pompeii: the famous body casts are plaster poured into hollows the victims left in the ash, a technique begun by Giuseppe Fiorelli in 1863 — making (ep028)
- Herculaneum: for centuries it was thought its people escaped, until hundreds of skeletons were found in the boathouses by the shore in the 1980s
- Akrotiri (prehistoric city): a Bronze Age town buried by the Minoan eruption where almost no bodies have been found, as if its people had warning
- Helike: a Greek city that sank in a single night in 373 BC, after an earthquake and a wave
- Thonis-Heracleion: Egypt's great port vanished under the sea and was only found by divers in 2000
- Port Royal (1692): an earthquake sent much of the pirate haven called "the wickedest city on Earth" into the sea
- Dunwich: once one of England's major ports, the medieval town has been taken by the sea, church by church
- Saint-Pierre, Martinique (1902): the "Paris of the Caribbean" was wiped out in minutes by Mount Pelée
- Roanoke Colony (1590): the only clue the vanished colonists left was the word "CROATOAN" carved into a post
- Ani: the "city of 1,001 churches" lies abandoned on the border of Turkey and Armenia
- Pavlopetri: one of the oldest known submerged towns lies a few meters under the sea off Greece

### Doomed Expeditions

- Franklin's lost expedition (1845): 129 men vanished in the Arctic, and their two ships were only found in 2014 and 2016
- Terra Nova expedition (1912): Scott's last three men died in their tent about 11 miles from a supply depot
- Andrée's Arctic balloon expedition (1897): their camp was found 33 years later, with film that could still be developed
- Burke and Wills expedition (1861): they staggered back to their base camp hours after the party waiting for them had left
- Karluk (ship) (1913): when the ship was trapped in ice, the expedition's leader left, and the rest were stranded on Wrangel Island
- Lady Franklin Bay Expedition (1884): only a handful of the 25 men were alive when the rescuers reached them
- Jeannette expedition (1881): a ship sent to find an open sea at the North Pole was crushed by ice instead
- 1924 British Mount Everest expedition: George Mallory's body was found 75 years later, and nobody knows if he reached the top

### Fallen Empires

- Fall of Constantinople (1453): by one account, the city fell through a small gate someone left open
- Sack of Rome (410): the first time in 800 years that a foreign enemy took the city of Rome
- Late Bronze Age collapse: around 1177 BC, nearly every great civilization of the eastern Mediterranean fell within a few decades
- Fall of Tenochtitlan (1521): smallpox killed huge numbers of the city's people before and during the siege
- Battle of the Teutoburg Forest (9 AD): three Roman legions were wiped out, and Augustus is said to have cried "Varus, give me back my legions!"
- Siege of Baghdad (1258): accounts say the Tigris ran black with ink from the books thrown into it
- Third Punic War (146 BC): Rome destroyed Carthage, but the story that it salted the earth appears to be a modern invention
- Library of Alexandria: it wasn't lost in one great fire, but declined over centuries

### Warnings Ignored

- SS Californian (1912): it was close enough to see the Titanic's rockets, but its radio operator had gone to bed
- Tay Bridge disaster (1879): the bridge fell in a gale with a train on it, and the inquiry found it badly designed, built, and maintained
- St. Francis Dam (1928): William Mulholland inspected a leak and judged the dam safe the day it collapsed
- Johnstown Flood (1889): the dam that failed belonged to a fishing club of Pittsburgh's richest men
- Great Molasses Flood (1919): the leaking tank had been painted brown to hide the leaks
- Sultana (steamboat) (1865): a boat built for a few hundred carried over 2,000 people, most of them freed Union prisoners, when its patched boiler exploded
- Triangle Shirtwaist Factory fire (1911): a stairway door was locked, and 146 garment workers died
- Iroquois Theatre fire (1903): advertised as "absolutely fireproof", it burned five weeks after opening
- Vasa (ship) (1628): the warship sank on its maiden voyage, less than a mile out, after failing a stability test before it sailed
- Knickerbocker Storm (1922): the roof of Washington's Knickerbocker Theatre collapsed under the snow during a film

### Sole Survivors

- Violet Jessop: a stewardess who survived the Titanic, the Britannic's sinking, and the Olympic's collision
- Tsutomu Yamaguchi (1945): the only person Japan officially recognized as surviving both atomic bombings
- Ludger Sylbaris (1902): one of the very few survivors of Mount Pelée's eruption, saved by the thick walls of his jail cell
- Charles Joughin (1912): the Titanic's chief baker survived a long time in the freezing water, and credited the whisky he had drunk
- Arthur John Priest: the "unsinkable stoker" survived the Titanic, the Britannic, and other sinkings
- Poon Lim (1942): a ship's steward survived 133 days alone on a raft in the Atlantic

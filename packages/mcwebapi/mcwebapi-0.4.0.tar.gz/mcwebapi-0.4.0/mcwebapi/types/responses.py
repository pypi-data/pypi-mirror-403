"""Dataclass definitions for Minecraft WebSocket API responses."""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


# ===== Common Types =====

@dataclass
class Position:
    """3D position coordinates."""
    x: float
    y: float
    z: float


@dataclass
class Rotation:
    """Entity rotation angles."""
    yaw: float
    pitch: float


@dataclass
class Velocity:
    """3D velocity vector."""
    x: float
    y: float
    z: float


# ===== Player Module Types =====

@dataclass
class Experience:
    """Player experience data."""
    level: int
    total: int
    progress: int


@dataclass
class ItemStack:
    """Inventory item information."""
    slot: int
    item: str
    count: int
    damage: int


@dataclass
class ItemStackExtended:
    """Extended inventory item with additional fields."""
    slot: int
    item: str
    count: int
    maxStackSize: int
    damage: Optional[int] = None
    maxDamage: Optional[int] = None
    displayName: Optional[str] = None


@dataclass
class MobEffect:
    """Active mob effect/potion effect."""
    effect: str
    amplifier: int
    duration: int


@dataclass
class AdvancementInfo:
    """Advancement information."""
    id: str
    completed: bool
    title: Optional[str] = None
    description: Optional[str] = None
    frame: Optional[str] = None
    hidden: Optional[bool] = None
    icon: Optional[str] = None
    completedDate: Optional[str] = None
    criteria: Optional[Dict[str, bool]] = None
    progress: Optional[str] = None
    percentage: Optional[float] = None


@dataclass
class Advancements:
    """All player advancements."""
    completed: List[AdvancementInfo]
    inProgress: List[AdvancementInfo]
    totalCompleted: int
    totalInProgress: int

    @classmethod
    def from_dict(cls, data: dict) -> 'Advancements':
        """Convert dict to Advancements dataclass."""
        return cls(
            completed=[AdvancementInfo(**adv) for adv in data.get('completed', [])],
            inProgress=[AdvancementInfo(**adv) for adv in data.get('inProgress', [])],
            totalCompleted=data['totalCompleted'],
            totalInProgress=data['totalInProgress']
        )


@dataclass
class PlayerInfo:
    """Complete player information."""
    name: str
    uuid: str
    health: float
    maxHealth: float
    food: int
    saturation: float
    level: int
    gameMode: str
    world: str
    x: float
    y: float
    z: float
    ping: int
    isSneaking: bool
    isSprinting: bool
    isFlying: bool


# ===== Block Module Types =====

@dataclass
class BlockInfo:
    """Block information at a position."""
    type: str
    x: int
    y: int
    z: int
    properties: Dict[str, str]
    lightLevel: int
    skyLight: int
    blockLight: int
    hasBlockEntity: bool
    blockEntityType: Optional[str] = None


@dataclass
class BlockInventory:
    """Block entity inventory information."""
    blockType: str
    hasBlockEntity: bool
    blockEntityType: Optional[str] = None
    error: Optional[str] = None
    hasBlockEntityType: Optional[bool] = None
    inventory: Optional[List[ItemStackExtended]] = None
    size: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'BlockInventory':
        """Convert dict to BlockInventory dataclass."""
        inventory = None
        if 'inventory' in data and data['inventory'] is not None:
            inventory = [ItemStackExtended(**item) for item in data['inventory']]

        return cls(
            blockType=data['blockType'],
            hasBlockEntity=data['hasBlockEntity'],
            blockEntityType=data.get('blockEntityType'),
            error=data.get('error'),
            hasBlockEntityType=data.get('hasBlockEntityType'),
            inventory=inventory,
            size=data.get('size')
        )


@dataclass
class FurnaceInfo:
    """Furnace block entity information."""
    type: str
    isBurning: bool
    burnTime: int
    cookTime: int
    cookTimeTotal: int
    input: Optional[str] = None
    inputCount: Optional[int] = None
    fuel: Optional[str] = None
    fuelCount: Optional[int] = None
    output: Optional[str] = None
    outputCount: Optional[int] = None


# ===== Entity Module Types =====

@dataclass
class EntitySpawnResult:
    """Result of entity spawn operation."""
    success: bool
    uuid: Optional[str] = None
    type: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    error: Optional[str] = None


@dataclass
class EntityInfo:
    """Detailed entity information."""
    uuid: str
    type: str
    x: float
    y: float
    z: float
    yaw: float
    pitch: float
    isAlive: bool
    isOnGround: bool
    isSilent: bool
    isGlowing: bool
    isInvulnerable: bool
    fireImmune: bool
    remainingFireTicks: int
    velocity: Velocity
    customName: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'EntityInfo':
        """Convert dict to EntityInfo dataclass."""
        velocity = Velocity(**data['velocity'])
        return cls(
            uuid=data['uuid'],
            type=data['type'],
            x=data['x'],
            y=data['y'],
            z=data['z'],
            yaw=data['yaw'],
            pitch=data['pitch'],
            isAlive=data['isAlive'],
            isOnGround=data['isOnGround'],
            isSilent=data['isSilent'],
            isGlowing=data['isGlowing'],
            isInvulnerable=data['isInvulnerable'],
            fireImmune=data['fireImmune'],
            remainingFireTicks=data['remainingFireTicks'],
            velocity=velocity,
            customName=data.get('customName')
        )


@dataclass
class EntitySummary:
    """Brief entity summary."""
    uuid: str
    type: str
    x: float
    y: float
    z: float
    isAlive: bool
    customName: Optional[str] = None


# ===== Level (World) Module Types =====

@dataclass
class BlockState:
    """Detailed block state information."""
    block: str
    properties: Any
    destroySpeed: float
    lightEmission: int


@dataclass
class Weather:
    """World weather information."""
    isRaining: bool
    isThundering: bool
    rainLevel: float
    thunderLevel: float


@dataclass
class WorldBorder:
    """World border configuration."""
    centerX: float
    centerZ: float
    size: float
    damagePerBlock: float
    damageSafeZone: float
    warningTime: int
    warningBlocks: int


@dataclass
class SpawnPoint:
    """World spawn point."""
    x: int
    y: int
    z: int
    angle: float


@dataclass
class LevelData:
    """Level metadata."""
    levelName: str
    hardcore: bool
    allowCommands: bool
    gameType: str


@dataclass
class ChunkInfo:
    """Chunk information."""
    isLoaded: bool
    inhabitedTime: int
    chunkX: int
    chunkZ: int


@dataclass
class LevelInfo:
    """Complete level information."""
    dimension: str
    seed: int
    dayTime: int
    totalTime: int
    raining: bool
    thundering: bool
    playerCount: int
    entityCount: Any
    difficulty: str


# ===== Server Module Types =====

@dataclass
class ServerInfo:
    """Server information."""
    version: str
    brand: str
    motd: str
    maxPlayers: int
    onlinePlayerCount: int
    difficulty: str
    isHardcore: bool
    defaultGameMode: str
    ticksRunning: int
    averageTPS: float


@dataclass
class MemoryUsage:
    """Server memory usage."""
    max: int
    total: int
    free: int
    used: int


@dataclass
class CommandResult:
    """Command execution result."""
    success: bool
    error: Optional[str] = None


# ===== Scoreboard Module Types =====

@dataclass
class ObjectiveInfo:
    """Scoreboard objective information."""
    name: str
    displayName: str
    criteria: str
    renderType: str


@dataclass
class TeamInfo:
    """Scoreboard team information."""
    name: str
    displayName: str
    color: str
    prefix: str
    suffix: str
    friendlyFire: bool
    seeFriendlyInvisibles: bool
    players: List[str]

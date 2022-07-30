import unrealsdk
import enum
import webbrowser
from typing import Dict, Iterable, List, Optional, cast

from Mods.ModMenu import (
    EnabledSaveType,
    Game,
    Keybind,
    KeybindManager,
    Mods,
    ModTypes,
    RegisterMod,
    SDKMod,
    ServerMethod,
)

# thank you apple :)
try:
    from Mods.EridiumLib import (
        checkLibraryVersion,
        checkModVersion,
        getCurrentWorldInfo,
        isClient,
        log,
    )
    from Mods.EridiumLib.keys import KeyBinds
except ImportError:
    webbrowser.open(
        "https://github.com/DAmNRelentless/bl2-eridiumlib/blob/main/docs/TROUBLESHOOTING.md"
    )
    raise

if __name__ == "__main__":
    import importlib
    import sys

    importlib.reload(sys.modules["Mods.EridiumLib"])
    importlib.reload(sys.modules["Mods.EridiumLib.keys"])

    # See https://github.com/bl-sdk/PythonSDK/issues/68
    try:
        raise NotImplementedError
    except NotImplementedError:
        __file__ = sys.exc_info()[-1].tb_frame.f_code.co_filename  # type: ignore


class MissionStatus(enum.IntEnum):
    NotStarted = 0
    Active = 1
    RequiredObjectivesComplete = 2
    ReadyToTurnIn = 3
    Complete = 4
    Failed = 5
    MAX = 6

    def canBeActivated(self) -> bool:
        """Returns true if the status is either ReadyToTurnIn or Active."""
        return self in [
            MissionStatus.ReadyToTurnIn,
            MissionStatus.Active,
        ]


class MissionSelector(SDKMod):
    Name: str = "Mission Selector"
    Author: str = "Chronophylos, Relentless"
    Description: str = "Switch through missions with hotkeys.\nInspired by Borderlands 3."
    Version: str = "1.3.2"
    _EridiumVersion: str = "0.4.2"

    SupportedGames: Game = Game.BL2 | Game.TPS
    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    SettingsInputs: Dict[str, str] = {
        KeyBinds.Enter.value: "Enable",
        KeyBinds.G.value: "GitHub",
    }

    def __init__(self) -> None:
        super().__init__()

        self.Keybinds = [
            Keybind(
                "Select next Mission", KeyBinds.RightBracket.value, True, OnPress=self.nextMission
            ),
            Keybind(
                "Select previous Mission",
                KeyBinds.LeftBracket.value,
                True,
                OnPress=self.prevMission,
            ),
        ]

    def Enable(self) -> None:
        super().Enable()

        if not checkLibraryVersion(self._EridiumVersion):
            raise RuntimeWarning("Incompatible EridiumLib version!")

        checkModVersion(self, "DAmNRelentless/bl2-missionselector")

    def SettingsInputPressed(self, action: str) -> None:
        if action == "GitHub":
            webbrowser.open("https://github.com/DAmNRelentless/bl2-missionselector")
        else:
            super().SettingsInputPressed(action)

    def nextMission(self, event: KeybindManager.InputEvent) -> None:
        if event != KeybindManager.InputEvent.Pressed:
            return

        missionTracker = self.getMissionTracker()
        activeMissions = cast(List[unrealsdk.UObject], self.getActiveMissions(missionTracker))
        index = self.getActiveMissionIndex(missionTracker, activeMissions)

        nextMission = None
        if index < len(activeMissions) - 1:
            nextMission = activeMissions[index + 1]
        else:
            nextMission = activeMissions[0]

        self.setActiveMission(nextMission.MissionDef)

    def prevMission(self, event: KeybindManager.InputEvent) -> None:
        if event != KeybindManager.InputEvent.Pressed:
            return

        missionTracker = self.getMissionTracker()
        activeMissions = cast(List[unrealsdk.UObject], self.getActiveMissions(missionTracker))
        index = self.getActiveMissionIndex(missionTracker, activeMissions)

        nextMission = activeMissions[index - 1]

        self.setActiveMission(nextMission.MissionDef)

    @staticmethod
    def getActiveMissionIndex(
        missionTracker: unrealsdk.UObject, missions: Iterable[unrealsdk.UObject]
    ) -> int:
        """Returns the index of the current active mission in missions."""
        activeMission = missionTracker.ActiveMission
        for index, mission in enumerate(missions):
            if mission.MissionDef.MissionNumber == activeMission.MissionNumber:
                return index
        return -1

    @staticmethod
    def getMissionTracker() -> unrealsdk.UObject:
        return cast(unrealsdk.UObject, getCurrentWorldInfo().GRI.MissionTracker)

    @staticmethod
    def getActiveMissions(
        missionTracker: unrealsdk.UObject,
    ) -> Iterable[unrealsdk.UObject]:
        """Returns all active missions sorted by their MissionNumber.

        For a definition of active see `MissionStatus.isActive`-
        """
        activeMissions = sorted(
            [m for m in missionTracker.MissionList if MissionStatus(m.Status).canBeActivated()],
            key=lambda m: int(m.MissionDef.MissionNumber),
        )

        return activeMissions

    def setActiveMission(self, mission: unrealsdk.UObject) -> None:
        """Set the currently tracked mission to mission."""
        if isClient():
            self._serverSetActiveMission(mission.MissionNumber)
        else:
            self._setActiveMission(mission.MissionNumber)

    def getMissionByNumber(
        self, missionTracker: unrealsdk.UObject, number: int
    ) -> unrealsdk.UObject:
        """Returns the mission with the MissionNumber equal to number.

        Raises an IndexError if the mission was not found.
        """
        for mission in missionTracker.MissionList:
            if mission.MissionDef.MissionNumber == number:
                return cast(unrealsdk.UObject, mission)
        raise IndexError(f"There is nomission with the mission number {number}")

    @ServerMethod
    def _serverSetActiveMission(self, number: int, PC: Optional[unrealsdk.UObject] = None) -> None:
        self._setActiveMission(number, PC)

    def _setActiveMission(self, number: int, PC: Optional[unrealsdk.UObject] = None) -> None:
        missionTracker = self.getMissionTracker()
        mission = self.getMissionByNumber(missionTracker, number)
        missionTracker.SetActiveMission(mission.MissionDef, True, PC)


instance = MissionSelector()
if __name__ == "__main__":
    log(instance, "Manually loaded")
    for mod in Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            Mods.remove(mod)
            log(instance, "Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break
RegisterMod(instance)

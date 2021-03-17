import unrealsdk
import enum
import webbrowser
from typing import Dict, List, Optional
from Mods.ModMenu import (
    SDKMod,
    Mods,
    ModTypes,
    EnabledSaveType,
    KeybindManager,
    Keybind,
    ServerMethod,
    RegisterMod,
)
from Mods.Eridium import KeyBinds, log

NEXT_MISSION_DESC: str = "Select next Mission"
NEXT_MISSION_KEY: str = KeyBinds.RightBracket
PREV_MISSION_DESC: str = "Select previous Mission"
PREV_MISSION_KEY: str = KeyBinds.LeftBracket


class EMissionStatus(enum.IntEnum):
    NotStarted = 0
    Active = 1
    RequiredObjectivesComplete = 2
    ReadyToTurnIn = 3
    Complete = 4
    Failed = 5
    MAX = 6

    def isActive(self) -> bool:
        return self in [
            EMissionStatus.ReadyToTurnIn,
            EMissionStatus.Active,
        ]


class MissionSelector(SDKMod):
    Name: str = "Mission Selector"
    Author: str = "Chronophylos"
    Description: str = "Switch through missions with hotkeys, like in BL3\n"
    Version: str = "1.2.0"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    SettingsInputs: Dict[str, str] = {"Enter": "Enable", "G": "Github"}

    def __init__(self) -> None:
        super().__init__()

        self.Keybinds = [
            Keybind(NEXT_MISSION_DESC, NEXT_MISSION_KEY),
            Keybind(PREV_MISSION_DESC, PREV_MISSION_KEY),
        ]

    def Enable(self) -> None:
        super().Enable()

        log(self, f"Version: {self.Version}")

    def GameInputPressed(
        self, bind: KeybindManager.Keybind, event: KeybindManager.InputEvent
    ) -> None:
        if event != KeybindManager.InputEvent.Pressed:
            return

        if bind.Name == NEXT_MISSION_DESC:
            self.NextMission()
        elif bind.Name == PREV_MISSION_DESC:
            self.PrevMission()

    def SettingsInputPressed(self, action: str) -> None:
        super().SettingsInputPressed(action)

        if action == "Github":
            webbrowser.open("https://github.com/Chronophylos/bl2_missionselector")

    def NextMission(self) -> None:
        missions = self.GetActiveMissions()
        active_mission_index = self._getActiveMissionIndex(missions)

        next_mission = None
        if active_mission_index < len(missions) - 1:
            next_mission = missions[active_mission_index + 1]
        else:
            next_mission = missions[0]

        self.SetSelectedMission(next_mission.missionDef)

    def PrevMission(self) -> None:
        missions = self.GetActiveMissions()
        active_mission_index = self._getActiveMissionIndex(missions)

        next_mission = missions[active_mission_index - 1]

        self.SetSelectedMission(next_mission.missionDef)

    def _isClient(self) -> bool:
        return int(unrealsdk.GetEngine().GetCurrentWorldInfo().NetMode) == 3

    def _getMissionTracker(self) -> unrealsdk.UObject:
        """Return the `WillowGame.MissionTracker`."""
        return unrealsdk.GetEngine().GetCurrentWorldInfo().GRI.MissionTracker

    def _getActiveMissionIndex(self, missions: List[unrealsdk.UObject]) -> int:
        active_mission = self.GetSelectedMission()
        for i, m in enumerate(missions):
            if m.MissionDef.MissionNumber == active_mission.MissionNumber:
                return i
        return -1

    def GetActiveMissions(self) -> List[unrealsdk.UObject]:
        """
        Get all missions that are either active or ready to turn in.
        Returns list of `IMission.MissionData`
        """
        missions = []
        for mission in self._getMissionTracker().MissionList:
            if EMissionStatus(mission.Status).isActive():
                missions.append(mission)
        return sorted(missions, key=lambda x: int(x.MissionDef.MissionNumber))

    def GetSelectedMission(self) -> unrealsdk.UObject:
        """Return the selected mission as `WillowGame.MissionDefinition`."""
        return self._getMissionTracker().GetActiveMission()

    def GetMissionByNumber(self, number: int) -> Optional[unrealsdk.UObject]:
        for mission in self._getMissionTracker().MissionList:
            if mission.MissionDef.MissionNumber == number:
                return mission.MissionDef
        return None

    def SetSelectedMission(self, mission: unrealsdk.UObject) -> None:
        """Sets the selected mission.

        mission must be a `WillowGame.MissionDefinition`.
        """

        if self._isClient():
            self._serverSetSelectedMission(mission.MissionNumber)
        else:
            self._setSelectedMission(mission.MissionNumber)

    @ServerMethod
    def _serverSetSelectedMission(
        self, number: int, PC: Optional[unrealsdk.UObject] = None
    ) -> None:
        self._setSelectedMission(number, PC)

    def _setSelectedMission(
        self, number: int, PC: Optional[unrealsdk.UObject] = None
    ) -> None:
        mission = self.GetMissionByNumber(number)
        if not mission:
            log(self, "Could not find mission with number {number}")
            return
        self._getMissionTracker().SetActiveMission(mission, True, PC)


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

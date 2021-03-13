import unrealsdk
import itertools
import enum
import webbrowser
from typing import Dict, List
from Mods.ModMenu import (
    SDKMod,
    Mods,
    RegisterMod,
    ModTypes,
    EnabledSaveType,
    KeybindManager,
    Keybind,
)

NEXT_MISSION_DESC: str = "Select next Mission"
NEXT_MISSION_KEY: str = "RightBracket"
PREV_MISSION_DESC: str = "Select previous Mission"
PREV_MISSION_KEY: str = "LeftBracket"


class EMissionStatus(enum.IntEnum):
    NotStarted = 0
    Active = enum.auto()
    RequiredObjectivesComplete = enum.auto()
    ReadyToTurnIn = enum.auto()
    Complete = enum.auto()
    Failed = enum.auto()
    MAX = enum.auto()


class MissionSelector(SDKMod):
    Name: str = "Mission Selector"
    Author: str = "Chronophylos"
    Description: str = "Switch through missions with hotkeys, like in BL3\n"
    Version: str = "1.1.1"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    SettingsInputs: Dict[str, str] = {"Enter": "Enable", "G": "Github"}

    def __init__(self) -> None:
        super().__init__()

        self.Keybinds = [
            # Keybind(NEXT_MISSION_DESC, NEXT_MISSION_KEY, OnPress=self.NextMission),
            # Keybind(PREV_MISSION_DESC, PREV_MISSION_KEY, OnPress=self.PrevMission),
            Keybind(NEXT_MISSION_DESC, NEXT_MISSION_KEY),
            Keybind(PREV_MISSION_DESC, PREV_MISSION_KEY),
        ]

    def _log(self, message: str) -> None:
        unrealsdk.Log(f"[{self.Name}] {message}")

    def Enable(self) -> None:
        super().Enable()

        self._log(f"Version: {self.Version}")

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
        activeMission = self._getSelectedMission()
        missions = self._getActiveMissions()

        activeMissionIndex = 0
        for i, m in enumerate(missions):
            if m.MissionDef.MissionNumber == activeMission.MissionNumber:
                activeMissionIndex = i
                break

        nextMission = None
        if activeMissionIndex < len(missions) - 1:
            nextMission = missions[activeMissionIndex + 1]
        else:
            nextMission = missions[0]

        self._setSelectedMission(nextMission.missionDef)

    def PrevMission(self) -> None:
        activeMission = self._getSelectedMission()
        missions = self._getActiveMissions()

        activeMissionIndex = 0
        for i, m in enumerate(missions):
            if m.MissionDef.MissionNumber == activeMission.MissionNumber:
                activeMissionIndex = i
                break

        nextMission = missions[activeMissionIndex - 1]

        self._setSelectedMission(nextMission.missionDef)

    def _getMissionTracker(self) -> unrealsdk.UObject:
        """Return the `WillowGame.MissionTracker`."""
        return unrealsdk.GetEngine().GetCurrentWorldInfo().GRI.MissionTracker

    def _getActiveMissions(self) -> List[unrealsdk.UObject]:
        """
        Get all missions that are either active or ready to turn in.
        Returns list of `IMission.MissionData`
        """
        missions = []
        for mission in self._getMissionTracker().MissionList:
            if mission.Status in [EMissionStatus.ReadyToTurnIn, EMissionStatus.Active]:
                missions.append(mission)
        return missions

    def _getSelectedMission(self) -> unrealsdk.UObject:
        """Returns the selected mission as `WillowGame.MissionDefinition`."""
        return self._getMissionTracker().GetActiveMission()

    def _setSelectedMission(self, missionDef: unrealsdk.UObject) -> None:
        """Sets the selected mission. mission must be a `WillowGame.MissionDefinition`."""
        self._getMissionTracker().SetActiveMission(missionDef)
        self._log(f"Set active mission to {missionDef.MissionName}")


instance = MissionSelector()
if __name__ == "__main__":
    instance._log(f"Manually loaded")
    for mod in Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            Mods.remove(mod)
            instance._log(f"Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break
RegisterMod(instance)
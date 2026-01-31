from pyPhases import PluginAdapter

from .RecordLoader import RecordLoader


class Plugin(PluginAdapter):
    def initPlugin(self):
        if "loader" not in self.project.config:
            self.project.config["loader"] = {}

        self.project.config["hasLoader"] = False
        self.project.on("prepared", self.loadLoader)

        def onConfigChanged(field):
            if field == "useLoader" or field is None:
                self.loadLoader()

        self.project.on("configChanged", onConfigChanged)

    def loadLoader(self):
        self.injectLoaderConfig(self.getConfig("useLoader"))

    def injectLoaderConfig(self, loaderId):
        # reload the model everytime the config changed
        self.logDebug("Load loader and all Config: %s" % loaderId)
        if loaderId is not None:
            loaderconfigs = self.getConfig("loader")
            if loaderId not in loaderconfigs:
                raise Exception(
                    "Loader with the id '%s' is not initialized, a specific loader plugin like pyPhasesRecordloaderSHHS needs to be loaded before the generic pyPhasesRecordloader, please reorder your plugins in the config."
                    % loaderId
                )

            loaderconfig = loaderconfigs[loaderId]
            if "baseloader" in loaderconfig:
                baseloader = loaderconfig["baseloader"]
                if baseloader not in loaderconfigs:
                    raise Exception(
                        f"Baseloader with the id {baseloader} is not initialized, a specific loader plugin like pyPhasesRecordloaderSHHS needs to be loaded before the generic pyPhasesRecordloader, please reorder your plugins in the config."
                    )
                self.project.config.update(loaderconfigs[loaderconfig["baseloader"]])

            self.project.config.update(loaderconfig)

            self.updateLoaderConfig()

    def updateLoaderConfig(self):
        self.project.config["hasLoader"] = True

        sourceChannels = self.getConfig("sourceChannels")

        # tailor sourceChannels to useSourceChannels
        useSourceChannels = self.project.getConfig("useSourceChannels", False)
        if bool(useSourceChannels):
            sourceChannels = [c for c in sourceChannels if c["name"] in useSourceChannels]
            if len(sourceChannels) == 0:
                raise Exception("No sourceChannels left after filtering by useSourceChannels.")

        self.project.config["sourceChannelNames"] = [
            c["name"] for c in sourceChannels if "generated" not in c or not c["generated"]
        ]
        self.project.config["sourceChannelTypes"] = [
            c["type"] for c in sourceChannels if "generated" not in c or not c["generated"]
        ]

        self.project.config["optionalSignals"] = [c["name"] for c in sourceChannels if "optional" in c and c["optional"]]
        aliasMap = {}
        for c in sourceChannels:
            if "aliases" in c:
                for a in c["aliases"]:
                    aliasMap[a] = c["name"]

        datasetConfig = self.getConfig("dataset")
        dataHandlerConfig = datasetConfig["downloader"] if "downloader" in datasetConfig else datasetConfig["dataHandler"]

        RecordLoader.recordLoader.set(
            name=self.getConfig("dataset.loaderName"),
            options={
                "filePath": self.getConfig("filePath"),
                "targetSignals": self.project.config["sourceChannelNames"],
                "targetSignalTypes": self.project.config["sourceChannelTypes"],
                "optionalSignals": self.project.config["optionalSignals"],
                "combineChannels": self.project.config["combineChannels"],
            },
            dynOptions={
                "chanelNameAliasMap": aliasMap,
                "dataHandlerConfig": dataHandlerConfig,
                "signalPath": dataHandlerConfig["signal-path"] if "signal-path" in dataHandlerConfig else "",
                "annotationPath": dataHandlerConfig["annotation-path"] if "annotation-path" in dataHandlerConfig else "",
                "metadataPath": dataHandlerConfig["metadata-path"] if "metadata-path" in dataHandlerConfig else "",
            },
        )
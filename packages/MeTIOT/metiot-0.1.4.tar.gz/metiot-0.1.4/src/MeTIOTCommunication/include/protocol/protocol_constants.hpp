#pragma once

#include <cstdint>

namespace Protocol {
    namespace ControllerHeader {
        enum class General : uint8_t {
            MalformedPacketNotification = 0xFF,
            DeviceIdentificationRequest = 0xFE,
        };

        enum class FishTank : uint8_t {

        };

        enum class FilterGuardian : uint8_t {
        
        };
    }

    namespace NodeHeader {
        enum class General : uint8_t {
            MalformedPacketNotification = 0xFF,
            DeviceIdentifier            = 0xFE,
            Data                        = 0xFD,
        };

        enum class FishTank : uint8_t {
        
        };

        enum class FilterGuardian : uint8_t {
        
        };
    }

    namespace DataSubHeader {
        enum class FishTank : uint8_t {
            Temperature                 = 0xFF, // Celcius
        };

        enum class FilterGuardian : uint8_t {
            FlowRate                    = 0xFF, // L/m
            Pressure                    = 0xFE, // PSI
        };
    }

    enum class DeviceIdentifier : uint8_t {
        FishTank                    = 0xFF,
        FilterGuardian              = 0xFE,
    };
}
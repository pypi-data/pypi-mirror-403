// SPDX-License-Identifier: Apache-2.0
// SPDX-FileCopyrightText: © 2025 Michael Pucher <contact@cluo.sh>
#pragma once
#include <string>

namespace ghidra {
class Architecture;
};

namespace reoxide {
class ReOxideInterface {
public:
    virtual ~ReOxideInterface() { };
    virtual void sendString(const std::string& s) = 0;
    virtual void disableInitialization() = 0;
    virtual void checkForPipelineUpdate(ghidra::Architecture&) = 0;
};
} // namespace reoxide

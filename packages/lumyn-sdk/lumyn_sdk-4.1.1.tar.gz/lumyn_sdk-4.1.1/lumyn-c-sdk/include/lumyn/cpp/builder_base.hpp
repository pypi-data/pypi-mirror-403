#pragma once

#include <string>
#include <string_view>
#include <optional>
#include <stdexcept>

namespace lumyn {

/**
 * @brief Pure abstract base class for all builder classes
 * 
 * This interface ensures consistent behavior across all builder types
 * Common functionality like execution tracking and validation is
 * handled through this base class.
 */
class ILumynBuilder {
public:
  virtual ~ILumynBuilder() = default;
  
  /**
   * @brief Execute the builder (must be implemented by derived classes)
   */
  virtual void execute() = 0;
  
  /**
   * @brief Check if builder has already been executed
   * @return true if executed, false otherwise
   */
  virtual bool isExecuted() const = 0;
  
protected:
  /**
   * @brief Mark builder as executed (called by derived classes)
   */
  virtual void markExecuted() = 0;
};

/**
 * @brief CRTP base class for builder implementations
 * 
 * Provides common functionality for zone/group targeting and execution tracking.
 * Derived classes should inherit from BuilderBase<DerivedClass> and implement
 * the execute() method with their specific logic.
 * 
 * @tparam Derived The derived builder class (CRTP pattern)
 */
template<typename Derived>
class BuilderBase : public ILumynBuilder {
public:
  /**
   * @brief Check if builder has already been executed
   * @return true if executed, false otherwise
   */
  bool isExecuted() const override { 
    return executed_; 
  }

protected:
  /**
   * @brief Mark builder as executed
   */
  void markExecuted() override { 
    executed_ = true; 
  }

  /**
   * @brief Check that builder hasn't been executed yet
   * @throws std::runtime_error if already executed
   */
  void checkNotExecuted() const {
    if (executed_) {
      throw std::runtime_error("Builder has already been executed");
    }
  }

  /**
   * @brief Set the target zone for this builder
   * @param zoneId The zone identifier
   * @return Reference to derived class for method chaining
   */
  Derived& setZone(std::string_view zoneId) {
    checkNotExecuted();
    zone_id_ = std::string(zoneId);
    group_id_.reset();
    return static_cast<Derived&>(*this);
  }

  /**
   * @brief Set the target group for this builder
   * @param groupId The group identifier
   * @return Reference to derived class for method chaining
   */
  Derived& setGroup(std::string_view groupId) {
    checkNotExecuted();
    group_id_ = std::string(groupId);
    zone_id_.reset();
    return static_cast<Derived&>(*this);
  }

  /**
   * @brief Validate that a target (zone or group) has been set
   * @throws std::runtime_error if neither zone nor group is set
   */
  void validateTarget() const {
    if (!zone_id_ && !group_id_) {
      throw std::runtime_error("Must call ForZone() or ForGroup() before executing");
    }
  }

  /**
   * @brief Get the zone ID if set
   * @return Optional containing zone ID, or empty if not set
   */
  const std::optional<std::string>& getZoneId() const {
    return zone_id_;
  }

  /**
   * @brief Get the group ID if set
   * @return Optional containing group ID, or empty if not set
   */
  const std::optional<std::string>& getGroupId() const {
    return group_id_;
  }

  /**
   * @brief Check if a zone is targeted
   * @return true if zone is set, false otherwise
   */
  bool hasZone() const {
    return zone_id_.has_value();
  }

  /**
   * @brief Check if a group is targeted
   * @return true if group is set, false otherwise
   */
  bool hasGroup() const {
    return group_id_.has_value();
  }

private:
  std::optional<std::string> zone_id_;
  std::optional<std::string> group_id_;
  bool executed_ = false;
};

} // namespace lumyn

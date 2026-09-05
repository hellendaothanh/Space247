```markdown
### 1. Thiết Lập Android Toolchain (Không Cần Android Studio)

Dành cho môi trường macOS chỉ sử dụng Android SDK Command-line Tools thay vì cài toàn bộ Android Studio.

#### Bước 1: Cài đặt công cụ và JDK qua Homebrew
```bash
brew install openjdk@17
brew install --cask android-commandlinetools

```

#### Bước 2: Cấu hình biến môi trường

Thêm các biến môi trường cần thiết vào file cấu hình zsh (`~/.zshrc`):

```bash
cat << 'EOF' >> ~/.zshrc

# Android SDK CLI Config
export ANDROID_HOME="/opt/homebrew/share/android-commandlinetools"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"
export JAVA_HOME="$(brew --prefix openjdk@17)"
EOF

source ~/.zshrc

```

#### Bước 3: Tải SDK components và cấp phép (Licenses)

```bash
# Cài đặt platform-tools, build-tools và Android API
sdkmanager --install "platform-tools" "build-tools;34.0.0" "platforms;android-34"

# Trỏ Flutter đến Android SDK và chấp nhận điều khoản
flutter config --android-sdk "$ANDROID_HOME"
flutter doctor --android-licenses

```

---

### 2. Thiết Lập & Khắc Phục Lỗi Môi Trường iOS

#### Bước 1: Cấu hình Xcode và CocoaPods

```bash
# Thiết lập đường dẫn developer tool cho Xcode
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -runFirstLaunch

# Cài đặt CocoaPods (nếu chưa có)
brew install cocoapods

```

#### Bước 2: Khởi tạo file `Podfile` chuẩn (iOS Target 15.0+)

Trường hợp thư mục `ios` chưa có `Podfile` hoặc gặp lỗi yêu cầu deployment target cao hơn:

```bash
cat << 'EOF' > ios/Podfile
platform :ios, '15.0'

ENV['COCOAPODS_DISABLE_STATS'] = 'true'

project 'Runner', {
  'Debug' => :debug,
  'Profile' => :release,
  'Release' => :release,
}

def flutter_root
  generated_xcode_build_settings_path = File.expand_path(File.join('..', 'Flutter', 'Generated.xcconfig'), __FILE__)
  unless File.exist?(generated_xcode_build_settings_path)
    raise "#{generated_xcode_build_settings_path} must exist. If you're running pod install manually, make sure flutter pub get has been executed."
  end

  File.foreach(generated_xcode_build_settings_path) do |line|
    matches = line.match(/FLUTTER_ROOT\=(.*)/)
    return matches[1].strip if matches
  end
  raise "FLUTTER_ROOT not found in #{generated_xcode_build_settings_path}. Try deleting Generated.xcconfig, then run flutter pub get"
end

require File.expand_path(File.join('packages', 'flutter_tools', 'bin', 'podhelper'), flutter_root)

flutter_ios_podfile_setup

target 'Runner' do
  use_frameworks!
  use_modular_headers!

  flutter_install_all_ios_pods File.dirname(File.realpath(__FILE__))
  target 'RunnerTests' do
    inherit! :search_paths
  end
end

post_install do |installer|
  installer.pods_project.targets.each do |target|
    flutter_additional_ios_build_settings(target)
  end
end
EOF

```

#### Bước 3: Đồng bộ Base Configuration cho CocoaPods

Tránh cảnh báo CocoaPods không set base configuration vào target `Runner`:

```bash
echo '#include? "Pods/Target Support Files/Pods-Runner/Pods-Runner.debug.xcconfig"' >> ios/Flutter/Debug.xcconfig
echo '#include? "Pods/Target Support Files/Pods-Runner/Pods-Runner.release.xcconfig"' >> ios/Flutter/Release.xcconfig
echo '#include? "Pods/Target Support Files/Pods-Runner/Pods-Runner.profile.xcconfig"' >> ios/Flutter/Profile.xcconfig

```

#### Bước 4: Cài đặt Native Pods

```bash
cd ios
pod repo update
pod install
cd ..

```

---

### 3. Kiểm Tra & Khởi Chạy Ứng Dụng

#### Kiểm tra lại toàn bộ môi trường:

```bash
flutter doctor

```

#### Dọn dẹp cache và khởi chạy trên iOS Simulator:

```bash
# Dọn dẹp artifact cũ
flutter clean
flutter pub get

# Mở máy ảo iOS và khởi chạy
open -a Simulator
flutter run
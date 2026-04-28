package com.zhaojiahao.resource.service;

import com.zhaojiahao.resource.entity.Resource;
import com.zhaojiahao.resource.entity.ResourceUserBehavior;
import com.zhaojiahao.resource.entity.User;
import com.zhaojiahao.resource.service.impl.ResourceEntityServiceImpl;
import com.zhaojiahao.resource.service.impl.ResourceUserBehaviorServiceImpl;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@Service
@RequiredArgsConstructor
public class SimulatedDataSeedService {

    private static final String DUMMY_FILE_PREFIX = "sim_res_";
    private static final String PASSWORD = "Seed1abcd";

    private static final String[] TOPICS = {
            "高等数学", "线性代数", "概率论与数理统计", "离散数学",
            "数据结构", "操作系统", "计算机网络", "数据库系统",
            "Java程序设计", "Python与人工智能基础"
    };

    private static final String[] FORMS = {
            "课件PPT", "期末复习提纲", "实验指导书", "课程设计参考",
            "历年真题汇编", "思维导图笔记", "上机实验代码包", "慕课配套讲义",
            "开卷资料整理", "小组作业范例"
    };

    // 文件类型及其对应的大小范围（字节）
    private static final String[] FILE_TYPES = {"pdf", "docx", "ppt", "xlsx", "jpg", "png", "zip", "mp4", "txt", "md"};
    private static final long[][] FILE_SIZE_RANGES = {
            {50 * 1024, 10 * 1024 * 1024},    // PDF: 50KB - 10MB
            {100 * 1024, 20 * 1024 * 1024},   // DOCX: 100KB - 20MB
            {500 * 1024, 50 * 1024 * 1024},   // PPT: 500KB - 50MB
            {50 * 1024, 5 * 1024 * 1024},     // XLSX: 50KB - 5MB
            {200 * 1024, 5 * 1024 * 1024},    // JPG: 200KB - 5MB
            {500 * 1024, 10 * 1024 * 1024},   // PNG: 500KB - 10MB
            {1 * 1024 * 1024, 100 * 1024 * 1024}, // ZIP: 1MB - 100MB
            {5 * 1024 * 1024, 500 * 1024 * 1024}, // MP4: 5MB - 500MB
            {10 * 1024, 2 * 1024 * 1024},     // TXT: 10KB - 2MB
            {5 * 1024, 1 * 1024 * 1024}       // MD: 5KB - 1MB
    };

    private static final Pattern USER_NUM = Pattern.compile("sim_(?:teacher|student)_(\\d+)");
    private static final Pattern RES_INDEX = Pattern.compile("sim_res_(\\d+)\\.[a-z0-9]+$");

    private final UserService userService;
    private final ResourceEntityServiceImpl resourceService;
    private final ResourceUserBehaviorServiceImpl behaviorService;

    @Value("${file.upload-path}")
    private String uploadPath;

    @Value("${seed.skip-if-exists:true}")
    private boolean skipIfExists;

    @Value("${seed.teacher-count:50}")
    private int teacherCount;

    @Value("${seed.student-count:300}")
    private int studentCount;

    @Value("${seed.resource-count:2000}")
    private int resourceCount;

    @Value("${seed.behavior-count:20000}")
    private int behaviorCount;

    @Transactional(rollbackFor = Exception.class)
    public void runSeed() throws IOException {
        if (skipIfExists && userService.lambdaQuery().eq(User::getUsername, "sim_teacher_0").exists()) {
            log.info("已存在 sim_teacher_0，跳过模拟数据导入（如需重做请清空相关用户/资源或设 seed.skip-if-exists=false）");
            return;
        }

        Path seedDir = Paths.get(uploadPath, "_seed");
        Files.createDirectories(seedDir);
        Path dummy = seedDir.resolve("dummy.txt");
        if (!Files.exists(dummy)) {
            Files.writeString(dummy, "毕设模拟资源占位文件（可安全删除 _seed 目录前请先清理库中对应记录）。\n", StandardCharsets.UTF_8);
        }
        String dummyAbs = dummy.toAbsolutePath().normalize().toString();
        long dummySize = Files.size(dummy);

        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        LocalDateTime now = LocalDateTime.now();

        log.info("开始导入模拟用户：教师 {} 人，学生 {} 人", teacherCount, studentCount);
        List<User> teachers = new ArrayList<>(teacherCount);
        for (int i = 0; i < teacherCount; i++) {
            User u = new User();
            u.setUsername("sim_teacher_" + i);
            u.setPassword(PASSWORD);
            u.setNickname("模拟教师" + i);
            u.setEmail("sim_t" + i + "@example.com");
            u.setRole("TEACHER");
            u.setStatus(1);
            u.setCreateTime(now);
            teachers.add(u);
        }
        userService.saveBatch(teachers, 100);

        List<User> students = new ArrayList<>(studentCount);
        for (int i = 0; i < studentCount; i++) {
            User u = new User();
            u.setUsername("sim_student_" + i);
            u.setPassword(PASSWORD);
            u.setNickname("模拟学生" + i);
            u.setEmail("sim_s" + i + "@example.com");
            u.setRole("STUDENT");
            u.setStatus(1);
            u.setCreateTime(now);
            students.add(u);
        }
        userService.saveBatch(students, 100);

        List<User> teacherRows = userService.lambdaQuery().likeRight(User::getUsername, "sim_teacher_").list();
        List<Long> teacherIds = teacherRows.stream().map(User::getId).sorted().toList();
        if (teacherIds.isEmpty()) {
            throw new IllegalStateException("未找到刚写入的模拟教师账号");
        }

        log.info("开始导入模拟资源 {} 条（分配真实文件类型和大小）", resourceCount);
        List<Resource> resources = new ArrayList<>(resourceCount);
        for (int i = 0; i < resourceCount; i++) {
            String topic = TOPICS[i % TOPICS.length];
            String form = FORMS[rnd.nextInt(FORMS.length)];

            // 随机选择文件类型
            int typeIndex = rnd.nextInt(FILE_TYPES.length);
            String fileType = FILE_TYPES[typeIndex];
            long[] sizeRange = FILE_SIZE_RANGES[typeIndex];

            // 在范围内随机生成文件大小（对数分布，更符合真实情况）
            long minSize = sizeRange[0];
            long maxSize = sizeRange[1];
            long fileSize;
            if (minSize == maxSize) {
                fileSize = minSize;
            } else {
                // 使用对数分布，小文件更多，大文件较少
                double logMin = Math.log(minSize);
                double logMax = Math.log(maxSize);
                double randomLog = logMin + rnd.nextDouble() * (logMax - logMin);
                fileSize = (long) Math.exp(randomLog);
            }

            Resource r = new Resource();
            r.setTitle(topic + "·" + form + "（编号" + i + "）");
            r.setFileName(DUMMY_FILE_PREFIX + i + "." + fileType);
            r.setFilePath(dummyAbs);
            r.setFileSize(fileSize);
            r.setFileType(fileType);
            r.setUploaderId(teacherIds.get(rnd.nextInt(teacherIds.size())));
            r.setCreateTime(now.minusDays(rnd.nextInt(120)));
            resources.add(r);
        }
        resourceService.saveBatch(resources, 500);

        List<Resource> resRows = resourceService.lambdaQuery()
                .likeRight(Resource::getFileName, DUMMY_FILE_PREFIX)
                .orderByAsc(Resource::getId)
                .list();

        List<Long> resourceIds = new ArrayList<>(resRows.size());
        List<Integer> resourceTopicMod = new ArrayList<>(resRows.size());
        for (Resource r : resRows) {
            resourceIds.add(r.getId());
            resourceTopicMod.add(parseResourceIndex(r.getFileName()) % TOPICS.length);
        }
        if (resourceIds.isEmpty()) {
            throw new IllegalStateException("未查询到模拟资源行");
        }

        List<User> allSimUsers = new ArrayList<>();
        allSimUsers.addAll(userService.lambdaQuery().likeRight(User::getUsername, "sim_teacher_").list());
        allSimUsers.addAll(userService.lambdaQuery().likeRight(User::getUsername, "sim_student_").list());

        log.info("开始导入模拟行为 {} 条（约 70% 与「用户编号偏好主题」相关，便于协同过滤）", behaviorCount);
        List<ResourceUserBehavior> behaviorBatch = new ArrayList<>(1000);
        for (int b = 0; b < behaviorCount; b++) {
            User u = allSimUsers.get(rnd.nextInt(allSimUsers.size()));
            int pref = userTopicPreference(u.getUsername());
            Long resId;
            if (rnd.nextDouble() < 0.7) {
                resId = pickResourceMatchingTopic(resourceIds, resourceTopicMod, pref, rnd);
            } else {
                resId = resourceIds.get(rnd.nextInt(resourceIds.size()));
            }
            ResourceUserBehavior row = new ResourceUserBehavior();
            row.setUserId(u.getId());
            row.setResourceId(resId);
            row.setActionType(rnd.nextDouble() < 0.65 ? "VIEW" : "DOWNLOAD");
            row.setCreateTime(now.minusHours(rnd.nextInt(24 * 60)));
            behaviorBatch.add(row);
            if (behaviorBatch.size() >= 1000) {
                behaviorService.saveBatch(behaviorBatch, 1000);
                behaviorBatch.clear();
            }
        }
        if (!behaviorBatch.isEmpty()) {
            behaviorService.saveBatch(behaviorBatch, 1000);
        }

        log.info("模拟数据导入完成。示例登录：sim_student_0 / {}，sim_teacher_0 / {}", PASSWORD, PASSWORD);
    }

    private static int userTopicPreference(String username) {
        Matcher m = USER_NUM.matcher(username);
        if (m.find()) {
            return Integer.parseInt(m.group(1)) % TOPICS.length;
        }
        return 0;
    }

    private static int parseResourceIndex(String fileName) {
        Matcher m = RES_INDEX.matcher(fileName);
        if (m.find()) {
            return Integer.parseInt(m.group(1));
        }
        return 0;
    }

    private static Long pickResourceMatchingTopic(
            List<Long> resourceIds,
            List<Integer> topicMod,
            int preferredTopic,
            ThreadLocalRandom rnd
    ) {
        List<Integer> idx = new ArrayList<>();
        for (int i = 0; i < topicMod.size(); i++) {
            if (topicMod.get(i) == preferredTopic) {
                idx.add(i);
            }
        }
        if (idx.isEmpty()) {
            return resourceIds.get(rnd.nextInt(resourceIds.size()));
        }
        return resourceIds.get(idx.get(rnd.nextInt(idx.size())));
    }

    /**
     * 为真实用户初始化行为数据（用于推荐系统）
     * 为每个真实用户添加随机行为记录，使他们能获得个性化推荐
     */
    @Transactional(rollbackFor = Exception.class)
    public void initRealUserBehaviors() {
        try {
            log.info("开始为真实用户初始化行为数据...");

            // 1. 获取所有非模拟用户
            List<User> realUsers = userService.lambdaQuery()
                    .notLike(User::getUsername, "sim_%")
                    .list();

            if (realUsers.isEmpty()) {
                log.info("未找到真实用户，跳过行为初始化");
                return;
            }

            // 2. 获取所有资源ID
            List<Resource> allResources = resourceService.list();
            if (allResources.isEmpty()) {
                log.warn("系统中无资源，无法初始化用户行为");
                return;
            }

            List<Long> resourceIds = allResources.stream()
                    .map(Resource::getId)
                    .collect(java.util.stream.Collectors.toList());

            ThreadLocalRandom rnd = ThreadLocalRandom.current();
            LocalDateTime now = LocalDateTime.now();

            // 3. 为每个真实用户添加行为记录
            int behaviorsPerUser = 20; // 每个用户20条行为记录
            List<ResourceUserBehavior> behaviors = new ArrayList<>();

            for (User user : realUsers) {
                // 检查用户是否已有行为记录
                long existingCount = behaviorService.lambdaQuery()
                        .eq(ResourceUserBehavior::getUserId, user.getId())
                        .count();

                if (existingCount > 0) {
                    log.debug("用户 {} 已有 {} 条行为记录，跳过", user.getUsername(), existingCount);
                    continue;
                }

                // 为用户添加随机行为记录
                for (int i = 0; i < behaviorsPerUser; i++) {
                    Long resourceId = resourceIds.get(rnd.nextInt(resourceIds.size()));
                    String actionType = rnd.nextDouble() < 0.7 ? "VIEW" : "DOWNLOAD";

                    ResourceUserBehavior behavior = new ResourceUserBehavior();
                    behavior.setUserId(user.getId());
                    behavior.setResourceId(resourceId);
                    behavior.setActionType(actionType);
                    behavior.setCreateTime(now.minusHours(rnd.nextInt(24 * 30))); // 过去30天内

                    behaviors.add(behavior);

                    if (behaviors.size() >= 1000) {
                        behaviorService.saveBatch(behaviors, 1000);
                        behaviors.clear();
                    }
                }

                log.info("为用户 {} 初始化 {} 条行为记录", user.getUsername(), behaviorsPerUser);
            }

            // 保存剩余的行为记录
            if (!behaviors.isEmpty()) {
                behaviorService.saveBatch(behaviors, 1000);
            }

            log.info("真实用户行为数据初始化完成，共处理 {} 个用户", realUsers.size());

        } catch (Exception e) {
            log.error("初始化真实用户行为数据失败", e);
            throw e;
        }
    }
}

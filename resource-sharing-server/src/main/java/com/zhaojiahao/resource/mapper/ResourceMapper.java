package com.zhaojiahao.resource.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhaojiahao.resource.entity.Resource;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface ResourceMapper extends BaseMapper<Resource> {

    /**
     * 查询热门资源（按交互次数排序）
     *
     * @param limit 限制数量
     * @return 热门资源列表
     */
    @Select("""
        SELECT r.*
        FROM resource r
        LEFT JOIN (
            SELECT resource_id, COUNT(*) as interaction_count
            FROM resource_user_behavior
            GROUP BY resource_id
        ) b ON r.id = b.resource_id
        WHERE LOCATE('sim_res_', r.file_name) <> 1  -- 排除种子占位文件（file_name 以 sim_res_ 开头）
        ORDER BY COALESCE(b.interaction_count, 0) DESC, r.create_time DESC
        LIMIT #{limit}
    """)
    List<Resource> selectPopularResources(int limit);

    /**
     * 查询随机资源
     *
     * @param limit 限制数量
     * @return 随机资源列表
     */
    @Select("""
        SELECT * FROM resource
        WHERE LOCATE('sim_res_', file_name) <> 1  -- 排除种子占位文件
        ORDER BY RAND()
        LIMIT #{limit}
    """)
    List<Resource> selectRandomResources(int limit);
}
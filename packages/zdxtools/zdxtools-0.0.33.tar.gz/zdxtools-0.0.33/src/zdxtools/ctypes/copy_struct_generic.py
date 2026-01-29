def copy_struct_generic(src, struct_type):
    dst = struct_type()
    # 使用反射来遍历所有字段并复制它们
    for field_name, field_type in struct_type._fields_:
        # 如果字段类型是指针，这里可能需要特殊处理
        # 但为了简单起见，我们直接复制值（对于指针，这可能不是好的做法）
        setattr(dst, field_name, getattr(src, field_name))

        # 或者，我们可以检查字段类型，并只对非指针类型进行复制
        # 但这需要更复杂的逻辑来识别指针类型

    return dst